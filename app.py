"""
SmilePhish — Plateforme de simulation de phishing multi-entreprises, avec planification
d'envoi et offres (essai gratuit / Pro).

Usage prévu : campagnes de sensibilisation au phishing menées par un consultant ou un
référent sécurité, pour le compte de sa propre organisation ou de ses clients, à
destination de collaborateurs dont la direction a autorisé le test.

IMPORTANT (lire avant usage) :
- Cette plateforme n'imite PAS la marque Microsoft/Outlook (pas de logo, pas de copie de
  page de connexion). La page cible affiche immédiatement un message de sensibilisation.
- Le domaine/compte d'envoi doit être un domaine que vous contrôlez (pas d'usurpation
  d'un domaine tiers). Cibler des adresses @outlook / @gmail / @yahoo / etc. est normal ;
  envoyer "depuis" l'un de ces domaines sans le contrôler ne l'est pas.
- Pour un ENVOI IMMÉDIAT, les identifiants SMTP ne sont jamais stockés sur disque.
- Pour un ENVOI PLANIFIÉ, les identifiants SMTP sont obligatoirement stockés (chiffrés,
  voir crypto_utils.py) car personne n'est présent pour les ressaisir au moment prévu.
"""

import os
import secrets
import csv
import io
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import (
    Flask, request, redirect, render_template, send_file, jsonify, Response,
    g, session, url_for,
)
from werkzeug.security import generate_password_hash, check_password_hash

import db as dbmod
import report_export
import mailer
import plans
import crypto_utils
import scheduler
from i18n import t, LANGUAGES, DEFAULT_LANG

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Base publique de la plateforme (celle que verront les liens dans les mails).
# A adapter : URL publique de votre serveur (ngrok, VM interne, etc.)
PUBLIC_BASE_URL = os.environ.get("SMILEPHISH_PUBLIC_URL", "http://127.0.0.1:5000")

app = Flask(__name__)
app.secret_key = os.environ.get("SMILEPHISH_SECRET_KEY") or secrets.token_hex(16)


# ---------------------------------------------------------------------------
# Base de données / contexte par requête
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = dbmod.connect()
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------
def current_lang():
    return session.get("lang", DEFAULT_LANG)


@app.context_processor
def inject_i18n():
    nav_user = None
    if session.get("user_id"):
        try:
            nav_user = get_db().execute(
                "SELECT id, role, display_name FROM users WHERE id=?", (session["user_id"],)
            ).fetchone()
        except Exception:
            nav_user = None
    return {
        "t": lambda key: t(key, current_lang()),
        "current_lang": current_lang(),
        "languages": LANGUAGES,
        "nav_user": nav_user,
    }


@app.route("/set-language", methods=["POST"])
def set_language():
    lang = request.form.get("lang", DEFAULT_LANG)
    if lang not in LANGUAGES:
        lang = DEFAULT_LANG
    session["lang"] = lang
    if session.get("user_id"):
        db = get_db()
        db.execute("UPDATE users SET lang=? WHERE id=?", (lang, session["user_id"]))
        db.commit()
    next_url = request.form.get("next") or url_for("index")
    return redirect(next_url)


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        # Vérifie que la session n'a pas été révoquée (limite de 2 connexions simultanées :
        # une 3e connexion fait expulser la plus ancienne session active).
        token = session.get("sess_token")
        if token and not dbmod.is_session_valid(get_db(), token):
            session.clear()
            return redirect(url_for("login", kicked="1"))
        if token:
            dbmod.touch_session(get_db(), token)
        return view(*args, **kwargs)
    return wrapped


def super_admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user["role"] != "super_admin":
            return "Accès réservé au super-administrateur", 403
        return view(*args, **kwargs)
    return wrapped


def company_admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user["role"] not in ("company_admin", "super_admin"):
            return "Accès réservé à l'administrateur de votre société", 403
        return view(*args, **kwargs)
    return wrapped


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return get_db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()


SUPERADMIN_BOOTSTRAP_EMAIL = (os.environ.get("SMILEPHISH_SUPERADMIN_EMAIL") or "").strip().lower()


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        db = get_db()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        display_name = request.form.get("display_name", "").strip()
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        declared_purpose = request.form.get("declared_purpose", "").strip()
        license_key = request.form.get("license_key", "").strip().upper()
        terms_accepted = request.form.get("terms_accepted") == "on"

        error_ctx = {
            "display_name": display_name, "full_name": full_name, "phone": phone,
            "declared_purpose": declared_purpose, "license_key": license_key,
        }

        if not terms_accepted:
            return render_template(
                "signup.html", error=t("err_terms_required", current_lang()), **error_ctx
            )
        if not full_name or not declared_purpose:
            return render_template(
                "signup.html", error=t("err_traceability_required", current_lang()), **error_ctx
            )

        existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            return render_template(
                "signup.html", error=t("err_email_taken", current_lang()), **error_ctx
            )

        is_super_admin = bool(SUPERADMIN_BOOTSTRAP_EMAIL) and email == SUPERADMIN_BOOTSTRAP_EMAIL
        company_id = None
        role = "company_admin"

        if is_super_admin:
            role = "super_admin"
        elif license_key:
            company = db.execute(
                "SELECT * FROM companies WHERE license_key=?", (license_key,)
            ).fetchone()
            if not company:
                return render_template(
                    "signup.html", error=t("err_license_invalid", current_lang()), **error_ctx
                )
            if company["status"] != "active":
                return render_template(
                    "signup.html", error=t("err_license_revoked", current_lang()), **error_ctx
                )
            seats_used = dbmod.company_seat_count(db, company["id"])
            if seats_used >= company["max_seats"]:
                return render_template(
                    "signup.html", error=t("err_license_full", current_lang()), **error_ctx
                )
            company_id = company["id"]
            role = "member"
        else:
            cur = db.execute(
                "INSERT INTO companies (name, license_plan, status, created_at) VALUES (?, 'free', 'active', ?)",
                (display_name or email, datetime.utcnow().isoformat()),
            )
            db.commit()
            company_id = cur.lastrowid

        pw_hash = generate_password_hash(password)
        cur = db.execute(
            """INSERT INTO users
               (email, password_hash, display_name, plan, lang, created_at,
                role, company_id, full_name, phone, declared_purpose,
                terms_accepted_at, terms_version)
               VALUES (?, ?, ?, 'free', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                email, pw_hash, display_name, current_lang(), datetime.utcnow().isoformat(),
                role, company_id, full_name, phone, declared_purpose,
                datetime.utcnow().isoformat(), dbmod.TERMS_VERSION,
            ),
        )
        db.commit()

        session["user_id"] = cur.lastrowid
        token = secrets.token_hex(24)
        session["sess_token"] = token
        dbmod.create_session(db, cur.lastrowid, token, request)
        return redirect(url_for("index"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        ok = bool(user) and check_password_hash(user["password_hash"], password)
        dbmod.log_login_attempt(db, user["id"] if user else None, email, ok, request)
        if not ok:
            return render_template("login.html", error=t("err_login", current_lang()))

        session["user_id"] = user["id"]
        session["lang"] = user["lang"] or DEFAULT_LANG
        token = secrets.token_hex(24)
        session["sess_token"] = token
        dbmod.create_session(db, user["id"], token, request)
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    token = session.get("sess_token")
    if token:
        get_db().execute("UPDATE user_sessions SET revoked=1 WHERE session_token=?", (token,))
        get_db().commit()
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Pages principales
# ---------------------------------------------------------------------------
@app.route("/")
@login_required
def index():
    db = get_db()
    user = current_user()
    orgs = db.execute(
        "SELECT * FROM organisations WHERE user_id=? ORDER BY name", (user["id"],)
    ).fetchall()

    org_groups = []
    for org in orgs:
        campaigns = db.execute(
            "SELECT * FROM campaigns WHERE organisation_id=? ORDER BY id DESC", (org["id"],)
        ).fetchall()
        cards = []
        for c in campaigns:
            cards.append({"campaign": c, "stats": dbmod.compute_stats(db, c["id"])})
        org_groups.append({"org": org, "cards": cards})

    lifetime_sent = dbmod.lifetime_sent_count(db, user["id"])
    effective_plan = dbmod.effective_plan(db, user)
    return render_template(
        "index.html",
        org_groups=org_groups,
        user=user,
        effective_plan=effective_plan,
        lifetime_sent=lifetime_sent,
        plan_limits=plans.limits_for(effective_plan),
    )


@app.route("/campaign/new", methods=["GET", "POST"])
@login_required
def new_campaign():
    db = get_db()
    user = current_user()
    orgs = db.execute(
        "SELECT * FROM organisations WHERE user_id=? ORDER BY name", (user["id"],)
    ).fetchall()

    if request.method == "POST":
        org_name = request.form.get("organisation_name", "").strip()
        org_id = request.form.get("organisation_id", "").strip()

        if org_id and org_id != "__new__":
            organisation = db.execute(
                "SELECT * FROM organisations WHERE id=? AND user_id=?", (org_id, user["id"])
            ).fetchone()
            if not organisation:
                return "Organisation invalide", 400
            organisation_id = organisation["id"]
        else:
            if not org_name:
                org_name = "Organisation sans nom"
            cur = db.execute(
                "INSERT INTO organisations (user_id, name, created_at) VALUES (?, ?, ?)",
                (user["id"], org_name, datetime.utcnow().isoformat()),
            )
            db.commit()
            organisation_id = cur.lastrowid

        cur = db.execute(
            """INSERT INTO campaigns
               (user_id, organisation_id, name, subject, sender_name, sender_email,
                html_template, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user["id"], organisation_id,
                request.form["name"],
                request.form["subject"],
                request.form["sender_name"],
                request.form["sender_email"],
                request.form["html_template"],
                datetime.utcnow().isoformat(),
            ),
        )
        db.commit()
        campaign_id = cur.lastrowid

        # Import des cibles (CSV collé dans un textarea : email,prenom,nom,departement),
        # tronqué au quota de destinataires par campagne de l'offre en cours.
        targets_raw = request.form.get("targets_csv", "").strip()
        rows = []
        for line in targets_raw.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            email = parts[0]
            first_name = parts[1] if len(parts) > 1 else ""
            last_name = parts[2] if len(parts) > 2 else ""
            department = parts[3] if len(parts) > 3 else ""
            token = secrets.token_urlsafe(16)
            rows.append((campaign_id, email, first_name, last_name, department, token))

        limit = plans.max_targets_per_campaign(dbmod.effective_plan(db, user))
        truncated = len(rows) > limit
        rows = rows[:limit]

        db.executemany(
            """INSERT INTO targets (campaign_id, email, first_name, last_name, department, token)
               VALUES (?, ?, ?, ?, ?, ?)""",
            rows,
        )
        db.commit()

        suffix = "?quota_truncated=1&limit=" + str(limit) if truncated else ""
        return redirect(f"/campaign/{campaign_id}{suffix}")

    return render_template(
        "new_campaign.html", orgs=orgs, user=user,
        plan_limits=plans.limits_for(dbmod.effective_plan(db, user)),
    )


def _get_owned_campaign_or_404(db, campaign_id, user_id):
    campaign = db.execute(
        "SELECT * FROM campaigns WHERE id=? AND user_id=?", (campaign_id, user_id)
    ).fetchone()
    return campaign


@app.route("/campaign/<int:campaign_id>")
@login_required
def campaign_detail(campaign_id):
    db = get_db()
    user = current_user()
    campaign = _get_owned_campaign_or_404(db, campaign_id, user["id"])
    if not campaign:
        return "Campagne introuvable", 404

    organisation = db.execute(
        "SELECT * FROM organisations WHERE id=?", (campaign["organisation_id"],)
    ).fetchone()
    stats = dbmod.compute_stats(db, campaign_id)
    per_user = dbmod.per_user_log(db, campaign_id)
    lifetime_sent = dbmod.lifetime_sent_count(db, user["id"])
    eff_plan = dbmod.effective_plan(db, user)

    return render_template(
        "dashboard.html",
        campaign=campaign,
        organisation=organisation,
        stats=stats,
        per_user=per_user,
        user=user,
        effective_plan=eff_plan,
        plan_limits=plans.limits_for(eff_plan),
        lifetime_sent=lifetime_sent,
        quota_truncated=request.args.get("quota_truncated"),
        quota_limit=request.args.get("limit"),
    )


# ---------------------------------------------------------------------------
# Envoi immédiat
# ---------------------------------------------------------------------------
@app.route("/campaign/<int:campaign_id>/send", methods=["POST"])
@login_required
def send_campaign(campaign_id):
    db = get_db()
    user = current_user()
    campaign = _get_owned_campaign_or_404(db, campaign_id, user["id"])
    if not campaign:
        return jsonify({"ok": False, "error": "Campagne introuvable"}), 404

    if campaign["admin_status"] == "suspended":
        return jsonify({
            "ok": False,
            "error": (
                "Cette campagne a été suspendue par l'administration de la plateforme"
                + (f" : {campaign['admin_reason']}" if campaign["admin_reason"] else ".")
            ),
        }), 403

    targets = db.execute(
        "SELECT * FROM targets WHERE campaign_id=? AND status='pending'", (campaign_id,)
    ).fetchall()

    smtp_params = {
        "smtp_host": request.form["smtp_host"],
        "smtp_port": request.form["smtp_port"],
        "smtp_user": request.form["smtp_user"],
        "smtp_pass": request.form["smtp_pass"],  # jamais persisté en DB pour un envoi immédiat
        "use_tls": request.form.get("use_tls") == "on",
        "delay_ms": request.form.get("delay_ms", 300),
    }

    eff_plan = dbmod.effective_plan(db, user)
    max_targets = plans.max_targets_per_campaign(eff_plan)
    max_lifetime = plans.max_lifetime_sent(eff_plan)
    if max_lifetime is not None:
        already_sent = dbmod.lifetime_sent_count(db, user["id"])
        remaining = max(0, max_lifetime - already_sent)
        max_targets = min(max_targets, remaining)
        if remaining == 0:
            return jsonify({
                "ok": False,
                "error": (
                    f"Quota de l'essai gratuit atteint ({max_lifetime} emails envoyés à vie). "
                    "Passez en Pro depuis la page \"Mon compte\" pour continuer."
                ),
            }), 403

    try:
        sent, rejected, errors = mailer.send_batch(
            db, campaign, targets, smtp_params, PUBLIC_BASE_URL, max_targets=max_targets
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    quota_note = None
    if max_targets < len(targets):
        quota_note = (
            f"Quota de votre offre atteint : seuls {max_targets} sur {len(targets)} "
            "destinataires ont été envoyés cette fois."
        )

    return jsonify(
        {"ok": True, "sent": sent, "rejected": rejected, "errors": errors, "quota_note": quota_note}
    )


# ---------------------------------------------------------------------------
# Planification d'un envoi futur
# ---------------------------------------------------------------------------
@app.route("/campaign/<int:campaign_id>/schedule", methods=["POST"])
@login_required
def schedule_campaign(campaign_id):
    db = get_db()
    user = current_user()
    campaign = _get_owned_campaign_or_404(db, campaign_id, user["id"])
    if not campaign:
        return jsonify({"ok": False, "error": "Campagne introuvable"}), 404
    if campaign["admin_status"] == "suspended":
        return jsonify({"ok": False, "error": "Cette campagne a été suspendue par l'administration de la plateforme."}), 403

    scheduled_at_raw = request.form.get("scheduled_at")  # format datetime-local : AAAA-MM-DDTHH:MM
    if not scheduled_at_raw:
        return jsonify({"ok": False, "error": "Date/heure manquante"}), 400
    try:
        scheduled_dt = datetime.fromisoformat(scheduled_at_raw)
    except ValueError:
        return jsonify({"ok": False, "error": "Date/heure invalide"}), 400

    smtp_pass = request.form["smtp_pass"]
    smtp_pass_enc = crypto_utils.encrypt(smtp_pass)

    db.execute(
        """UPDATE campaigns SET
             scheduled_at=?, schedule_status='scheduled', schedule_error=NULL,
             smtp_host=?, smtp_port=?, smtp_user=?, smtp_pass_enc=?,
             smtp_use_tls=?, smtp_delay_ms=?
           WHERE id=?""",
        (
            scheduled_dt.isoformat(),
            request.form["smtp_host"],
            int(request.form["smtp_port"]),
            request.form["smtp_user"],
            smtp_pass_enc,
            1 if request.form.get("use_tls") == "on" else 0,
            int(request.form.get("delay_ms", 300) or 300),
            campaign_id,
        ),
    )
    db.commit()

    return jsonify({"ok": True, "scheduled_at": dbmod.fmt_dt(scheduled_dt.isoformat())})


@app.route("/campaign/<int:campaign_id>/schedule/cancel", methods=["POST"])
@login_required
def cancel_schedule(campaign_id):
    db = get_db()
    user = current_user()
    campaign = _get_owned_campaign_or_404(db, campaign_id, user["id"])
    if not campaign:
        return jsonify({"ok": False, "error": "Campagne introuvable"}), 404

    db.execute(
        "UPDATE campaigns SET schedule_status='cancelled' WHERE id=?", (campaign_id,)
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/schedules")
@login_required
def schedules():
    db = get_db()
    user = current_user()
    rows = db.execute(
        """SELECT campaigns.*, organisations.name AS org_name
           FROM campaigns
           JOIN organisations ON organisations.id = campaigns.organisation_id
           WHERE campaigns.user_id=? AND campaigns.schedule_status != 'none'
           ORDER BY campaigns.scheduled_at DESC""",
        (user["id"],),
    ).fetchall()
    items = []
    for r in rows:
        items.append({
            "campaign": r,
            "org_name": r["org_name"],
            "scheduled_at_fmt": dbmod.fmt_dt(r["scheduled_at"]),
        })
    return render_template("schedules.html", items=items, user=user)


# ---------------------------------------------------------------------------
# Compte / société / licence
# ---------------------------------------------------------------------------
@app.route("/account")
@login_required
def account():
    db = get_db()
    user = current_user()
    lifetime_sent = dbmod.lifetime_sent_count(db, user["id"])
    company = None
    seats_used = 0
    if user["company_id"]:
        company = db.execute("SELECT * FROM companies WHERE id=?", (user["company_id"],)).fetchone()
        seats_used = dbmod.company_seat_count(db, user["company_id"])
    eff_plan = dbmod.effective_plan(db, user)
    return render_template(
        "account.html", user=user, lifetime_sent=lifetime_sent,
        company=company, seats_used=seats_used, effective_plan=eff_plan,
        plan_limits=plans.limits_for(eff_plan),
        license_durations=plans.LICENSE_DURATIONS,
    )


@app.route("/company/subscribe", methods=["POST"])
@company_admin_required
def company_subscribe():
    """Souscription (démo) : génère/renouvelle la licence Pro de la société du compte
    connecté pour la durée choisie. Aucune passerelle de paiement réelle n'est branchée
    ici — à remplacer avant tout usage commercial."""
    db = get_db()
    user = current_user()
    if not user["company_id"]:
        return "Aucune société associée à ce compte", 400

    try:
        duration_months = int(request.form["duration_months"])
    except (KeyError, ValueError):
        return "Durée invalide", 400
    if duration_months not in plans.LICENSE_DURATIONS:
        return "Durée invalide", 400

    company = db.execute("SELECT * FROM companies WHERE id=?", (user["company_id"],)).fetchone()
    now = datetime.utcnow()
    expires = now + timedelta(days=30 * duration_months)

    license_key = company["license_key"] or dbmod.generate_license_key()
    db.execute(
        """UPDATE companies SET
             license_key=?, license_plan='pro', license_duration_months=?,
             license_starts_at=?, license_expires_at=?, status='active'
           WHERE id=?""",
        (license_key, duration_months, now.isoformat(), expires.isoformat(), company["id"]),
    )
    db.commit()
    return redirect(url_for("account"))


@app.route("/terms")
def terms():
    return render_template("terms.html", terms_version=dbmod.TERMS_VERSION)


# ---------------------------------------------------------------------------
# Assistance (tickets, pas de prise de main à distance réelle)
# ---------------------------------------------------------------------------
@app.route("/support", methods=["GET", "POST"])
@login_required
def support():
    db = get_db()
    user = current_user()
    if request.method == "POST":
        db.execute(
            """INSERT INTO support_tickets (user_id, subject, message, urgency, status, created_at)
               VALUES (?, ?, ?, ?, 'open', ?)""",
            (
                user["id"], request.form["subject"], request.form["message"],
                request.form.get("urgency", "normal"), datetime.utcnow().isoformat(),
            ),
        )
        db.commit()

    tickets = db.execute(
        "SELECT * FROM support_tickets WHERE user_id=? ORDER BY id DESC", (user["id"],)
    ).fetchall()
    return render_template("support.html", tickets=tickets, user=user)


# ---------------------------------------------------------------------------
# Mises à jour de la plateforme (bannière d'information + accusé de réception)
# ---------------------------------------------------------------------------
def pending_update_for(db, user):
    if not user:
        return None
    row = db.execute(
        """SELECT * FROM platform_updates
           WHERE id NOT IN (SELECT update_id FROM user_update_acks WHERE user_id=?)
           ORDER BY id DESC LIMIT 1""",
        (user["id"],),
    ).fetchone()
    return row


@app.context_processor
def inject_pending_update():
    user = current_user() if session.get("user_id") else None
    if not user:
        return {"pending_update": None}
    return {"pending_update": pending_update_for(get_db(), user)}


@app.route("/updates/ack/<int:update_id>", methods=["POST"])
@login_required
def ack_update(update_id):
    db = get_db()
    user = current_user()
    db.execute(
        "INSERT OR IGNORE INTO user_update_acks (user_id, update_id, acked_at) VALUES (?, ?, ?)",
        (user["id"], update_id, datetime.utcnow().isoformat()),
    )
    db.commit()
    return redirect(request.referrer or url_for("index"))


# ---------------------------------------------------------------------------
# Super-administration
# ---------------------------------------------------------------------------
@app.route("/superadmin")
@super_admin_required
def superadmin_dashboard():
    db = get_db()
    rows = db.execute(
        """SELECT campaigns.*, organisations.name AS org_name, users.email AS owner_email,
                  users.display_name AS owner_company, companies.name AS subscriber_name
           FROM campaigns
           JOIN organisations ON organisations.id = campaigns.organisation_id
           JOIN users ON users.id = campaigns.user_id
           LEFT JOIN companies ON companies.id = users.company_id
           ORDER BY campaigns.id DESC"""
    ).fetchall()
    items = []
    for r in rows:
        items.append({"campaign": r, "stats": dbmod.compute_stats(db, r["id"])})
    return render_template("superadmin.html", items=items)


@app.route("/superadmin/campaign/<int:campaign_id>/sanction", methods=["POST"])
@super_admin_required
def superadmin_sanction(campaign_id):
    db = get_db()
    user = current_user()
    action = request.form.get("action")  # suspend | reactivate
    reason = request.form.get("reason", "").strip()
    new_status = "suspended" if action == "suspend" else "active"
    db.execute(
        "UPDATE campaigns SET admin_status=?, admin_reason=?, admin_by=?, admin_at=? WHERE id=?",
        (new_status, reason or None, user["id"], datetime.utcnow().isoformat(), campaign_id),
    )
    db.commit()
    return redirect(url_for("superadmin_dashboard"))


@app.route("/superadmin/companies")
@super_admin_required
def superadmin_companies():
    db = get_db()
    companies = db.execute("SELECT * FROM companies ORDER BY id DESC").fetchall()
    items = []
    for c in companies:
        items.append({"company": c, "seats_used": dbmod.company_seat_count(db, c["id"])})
    return render_template("superadmin_companies.html", items=items)


@app.route("/superadmin/company/<int:company_id>/reset-key", methods=["POST"])
@super_admin_required
def superadmin_reset_key(company_id):
    db = get_db()
    new_key = dbmod.generate_license_key()
    db.execute("UPDATE companies SET license_key=? WHERE id=?", (new_key, company_id))
    db.commit()
    return redirect(url_for("superadmin_companies"))


@app.route("/superadmin/company/<int:company_id>/toggle-status", methods=["POST"])
@super_admin_required
def superadmin_toggle_company(company_id):
    db = get_db()
    company = db.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
    new_status = "revoked" if company["status"] == "active" else "active"
    db.execute("UPDATE companies SET status=? WHERE id=?", (new_status, company_id))
    db.commit()
    return redirect(url_for("superadmin_companies"))


@app.route("/superadmin/audit")
@super_admin_required
def superadmin_audit():
    db = get_db()
    rows = db.execute(
        """SELECT login_audit.*, users.email AS user_email
           FROM login_audit LEFT JOIN users ON users.id = login_audit.user_id
           ORDER BY login_audit.id DESC LIMIT 300"""
    ).fetchall()
    return render_template("superadmin_audit.html", rows=rows, scope_label="Toute la plateforme")


@app.route("/audit")
@company_admin_required
def company_audit():
    db = get_db()
    user = current_user()
    if user["role"] == "super_admin":
        return redirect(url_for("superadmin_audit"))
    rows = db.execute(
        """SELECT login_audit.*, users.email AS user_email
           FROM login_audit LEFT JOIN users ON users.id = login_audit.user_id
           WHERE users.company_id=?
           ORDER BY login_audit.id DESC LIMIT 300""",
        (user["company_id"],),
    ).fetchall()
    return render_template("superadmin_audit.html", rows=rows, scope_label="Votre société")


@app.route("/superadmin/updates", methods=["GET", "POST"])
@super_admin_required
def superadmin_updates():
    db = get_db()
    user = current_user()
    if request.method == "POST":
        db.execute(
            """INSERT INTO platform_updates (version, title, description, required_action, created_at, created_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                request.form["version"], request.form["title"], request.form["description"],
                request.form.get("required_action", ""), datetime.utcnow().isoformat(), user["id"],
            ),
        )
        db.commit()
    updates = db.execute("SELECT * FROM platform_updates ORDER BY id DESC").fetchall()
    return render_template("superadmin_updates.html", updates=updates)


@app.route("/superadmin/support")
@super_admin_required
def superadmin_support():
    db = get_db()
    rows = db.execute(
        """SELECT support_tickets.*, users.email AS user_email
           FROM support_tickets JOIN users ON users.id = support_tickets.user_id
           ORDER BY support_tickets.id DESC"""
    ).fetchall()
    return render_template("superadmin_support.html", rows=rows)


@app.route("/superadmin/support/<int:ticket_id>/close", methods=["POST"])
@super_admin_required
def superadmin_close_ticket(ticket_id):
    db = get_db()
    db.execute(
        "UPDATE support_tickets SET status='closed', updated_at=? WHERE id=?",
        (datetime.utcnow().isoformat(), ticket_id),
    )
    db.commit()
    return redirect(url_for("superadmin_support"))


# ---------------------------------------------------------------------------
# Tracking (public, pas d'authentification : ce sont les destinataires qui cliquent)
# ---------------------------------------------------------------------------
@app.route("/track/open/<token>.png")
def track_open(token):
    db = get_db()
    target = db.execute("SELECT * FROM targets WHERE token=?", (token,)).fetchone()
    if target:
        log_event(db, target["id"], "open", request)
    return Response(mailer.TRANSPARENT_PNG, mimetype="image/png")


@app.route("/track/click/<token>")
def track_click(token):
    db = get_db()
    target = db.execute("SELECT * FROM targets WHERE token=?", (token,)).fetchone()
    if target:
        log_event(db, target["id"], "click", request)
        return redirect(f"/awareness/{token}")
    return "Lien invalide", 404


@app.route("/awareness/<token>", methods=["GET", "POST"])
def awareness(token):
    db = get_db()
    target = db.execute("SELECT * FROM targets WHERE token=?", (token,)).fetchone()
    if not target:
        return "Lien invalide", 404

    if request.method == "POST":
        log_event(db, target["id"], "submit", request)
        return redirect(f"/awareness/{token}")

    campaign = db.execute(
        "SELECT * FROM campaigns WHERE id=?", (target["campaign_id"],)
    ).fetchone()
    owner = db.execute("SELECT * FROM users WHERE id=?", (campaign["user_id"],)).fetchone()
    awareness_lang = (owner["lang"] if owner else None) or DEFAULT_LANG
    aw = {
        "lang": awareness_lang,
        "title": t("awareness_title", awareness_lang),
        "body": t("awareness_body", awareness_lang),
        "tips_title": t("awareness_tips_title", awareness_lang),
        "ack": t("awareness_ack", awareness_lang),
    }
    return render_template("awareness.html", target=target, aw=aw)


def log_event(db, target_id, event_type, req):
    db.execute(
        """INSERT INTO events (target_id, event_type, created_at, ip_address, user_agent, extra)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            target_id,
            event_type,
            datetime.utcnow().isoformat(),
            req.remote_addr,
            req.headers.get("User-Agent", ""),
            "",
        ),
    )
    db.commit()


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
@app.route("/campaign/<int:campaign_id>/export.csv")
@login_required
def export_csv(campaign_id):
    db = get_db()
    user = current_user()
    campaign = _get_owned_campaign_or_404(db, campaign_id, user["id"])
    if not campaign:
        return "Campagne introuvable", 404
    rows = dbmod.per_user_log(db, campaign_id)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["Email", "Prenom", "Nom", "Departement", "Statut envoi", "Ouvert", "Clique", "Soumis", "Premier clic"]
    )
    for r in rows:
        writer.writerow(
            [
                r["email"], r["first_name"], r["last_name"], r["department"], r["status"],
                "Oui" if r["opened"] else "Non",
                "Oui" if r["clicked"] else "Non",
                "Oui" if r["submitted"] else "Non",
                r["first_click_at"] or "",
            ]
        )
    buf.seek(0)
    return send_file(
        io.BytesIO(buf.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"SmilePhish_{campaign_id}_rapport.csv",
    )


def _export_common(campaign_id):
    db = get_db()
    user = current_user()
    campaign = _get_owned_campaign_or_404(db, campaign_id, user["id"])
    if not campaign:
        return None, None, None
    campaign = dict(campaign)
    org = db.execute(
        "SELECT name FROM organisations WHERE id=?", (campaign["organisation_id"],)
    ).fetchone()
    campaign["organisation_name"] = org["name"] if org else ""
    stats = dbmod.compute_stats(db, campaign_id)
    rows = dbmod.per_user_log(db, campaign_id)
    return campaign, stats, rows


@app.route("/campaign/<int:campaign_id>/export.xlsx")
@login_required
def export_xlsx(campaign_id):
    campaign, stats, rows = _export_common(campaign_id)
    if campaign is None:
        return "Campagne introuvable", 404
    buf = report_export.build_xlsx(campaign, stats, rows)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"SmilePhish_{campaign_id}_rapport.xlsx",
    )


@app.route("/campaign/<int:campaign_id>/export.docx")
@login_required
def export_docx(campaign_id):
    campaign, stats, rows = _export_common(campaign_id)
    if campaign is None:
        return "Campagne introuvable", 404
    buf = report_export.build_docx(campaign, stats, rows)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=f"SmilePhish_{campaign_id}_rapport.docx",
    )


@app.route("/campaign/<int:campaign_id>/export.pdf")
@login_required
def export_pdf(campaign_id):
    campaign, stats, rows = _export_common(campaign_id)
    if campaign is None:
        return "Campagne introuvable", 404
    buf = report_export.build_pdf(campaign, stats, rows)
    return send_file(
        buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"SmilePhish_{campaign_id}_rapport.pdf",
    )


@app.route("/campaign/<int:campaign_id>/export.html")
@login_required
def export_html(campaign_id):
    campaign, stats, rows = _export_common(campaign_id)
    if campaign is None:
        return "Campagne introuvable", 404
    html = report_export.build_html(campaign, stats, rows)
    buf = io.BytesIO(html.encode("utf-8"))
    return send_file(
        buf,
        mimetype="text/html",
        as_attachment=True,
        download_name=f"SmilePhish_{campaign_id}_rapport.html",
    )


if __name__ == "__main__":
    dbmod.init_db()
    scheduler.start(PUBLIC_BASE_URL)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
