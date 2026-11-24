"""
Schéma de base de données et helpers communs pour SmilePhish.

Multi-tenant : chaque compte utilisateur (consultant / référent sécurité) peut créer
plusieurs "organisations" (ses entreprises clientes). Chaque campagne est rattachée à
une organisation, elle-même rattachée à un compte utilisateur. Les données d'un compte
ne sont jamais visibles par un autre compte.
"""

import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "smilephish.db")


def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            plan TEXT NOT NULL DEFAULT 'free',   -- free | pro
            lang TEXT NOT NULL DEFAULT 'fr',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS organisations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            organisation_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            sender_name TEXT NOT NULL,
            sender_email TEXT NOT NULL,
            html_template TEXT NOT NULL,
            created_at TEXT NOT NULL,
            -- Planification (NULL = jamais planifiée, envoi manuel classique)
            scheduled_at TEXT,
            schedule_status TEXT NOT NULL DEFAULT 'none',  -- none|scheduled|sent|failed|cancelled
            schedule_error TEXT,
            smtp_host TEXT,
            smtp_port INTEGER,
            smtp_user TEXT,
            smtp_pass_enc TEXT,
            smtp_use_tls INTEGER DEFAULT 1,
            smtp_delay_ms INTEGER DEFAULT 300,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (organisation_id) REFERENCES organisations(id)
        );

        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            department TEXT,
            token TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',  -- pending, sent, rejected
            sent_at TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,  -- open, click, submit
            created_at TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            extra TEXT,
            FOREIGN KEY (target_id) REFERENCES targets(id)
        );

        -- Société abonnée (licence), distincte des "organisations" (entreprises CIBLES
        -- des campagnes). Une société abonnée possède une clé de licence et jusqu'à
        -- 5 comptes utilisateurs internes (ses collaborateurs).
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            license_key TEXT UNIQUE,
            license_plan TEXT NOT NULL DEFAULT 'free',     -- free | pro
            license_duration_months INTEGER,
            license_starts_at TEXT,
            license_expires_at TEXT,
            max_seats INTEGER NOT NULL DEFAULT 5,
            status TEXT NOT NULL DEFAULT 'active',          -- active | revoked
            created_at TEXT NOT NULL
        );

        -- Piste d'audit des connexions (succès ET échecs), jamais purgée automatiquement.
        CREATE TABLE IF NOT EXISTS login_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email_attempted TEXT,
            success INTEGER NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL
        );

        -- Sessions actives, pour limiter à 2 connexions simultanées par compte.
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            revoked INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Notes de mise à jour de la plateforme, à accuser réception par chaque compte.
        CREATE TABLE IF NOT EXISTS platform_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            required_action TEXT,
            created_at TEXT NOT NULL,
            created_by INTEGER
        );

        CREATE TABLE IF NOT EXISTS user_update_acks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            update_id INTEGER NOT NULL,
            acked_at TEXT NOT NULL,
            UNIQUE(user_id, update_id)
        );

        -- Tickets d'assistance (support à distance = prise en charge asynchrone, pas de
        -- prise de main à distance réelle intégrée ici).
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            urgency TEXT NOT NULL DEFAULT 'normal',   -- low|normal|high
            status TEXT NOT NULL DEFAULT 'open',       -- open|in_progress|closed
            created_at TEXT NOT NULL,
            updated_at TEXT
        );
        """
    )
    conn.commit()

    # --- Migration légère : ajout de colonnes sur des tables déjà existantes (bases
    # créées par une version antérieure de SmilePhish). Sans danger si déjà présentes.
    _ensure_column(conn, "users", "role", "TEXT NOT NULL DEFAULT 'company_admin'")
    _ensure_column(conn, "users", "company_id", "INTEGER")
    _ensure_column(conn, "users", "full_name", "TEXT")
    _ensure_column(conn, "users", "phone", "TEXT")
    _ensure_column(conn, "users", "declared_purpose", "TEXT")
    _ensure_column(conn, "users", "terms_accepted_at", "TEXT")
    _ensure_column(conn, "users", "terms_version", "TEXT")

    _ensure_column(conn, "campaigns", "admin_status", "TEXT NOT NULL DEFAULT 'active'")
    _ensure_column(conn, "campaigns", "admin_reason", "TEXT")
    _ensure_column(conn, "campaigns", "admin_by", "INTEGER")
    _ensure_column(conn, "campaigns", "admin_at", "TEXT")

    conn.commit()
    conn.close()


def _ensure_column(conn, table, column, declaration):
    cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")


TERMS_VERSION = "2026-11-23"


def fmt_dt(iso_str):
    """Formate un timestamp ISO UTC stocké en 'JJ/MM/AAAA HH:MM:SS' lisible."""
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except ValueError:
        return iso_str


def compute_stats(db, campaign_id):
    total = db.execute(
        "SELECT COUNT(*) c FROM targets WHERE campaign_id=?", (campaign_id,)
    ).fetchone()["c"]
    sent = db.execute(
        "SELECT COUNT(*) c FROM targets WHERE campaign_id=? AND status='sent'", (campaign_id,)
    ).fetchone()["c"]
    rejected = db.execute(
        "SELECT COUNT(*) c FROM targets WHERE campaign_id=? AND status='rejected'", (campaign_id,)
    ).fetchone()["c"]

    opened = db.execute(
        """SELECT COUNT(DISTINCT target_id) c FROM events
           WHERE event_type='open' AND target_id IN (SELECT id FROM targets WHERE campaign_id=?)""",
        (campaign_id,),
    ).fetchone()["c"]
    clicked = db.execute(
        """SELECT COUNT(DISTINCT target_id) c FROM events
           WHERE event_type='click' AND target_id IN (SELECT id FROM targets WHERE campaign_id=?)""",
        (campaign_id,),
    ).fetchone()["c"]
    submitted = db.execute(
        """SELECT COUNT(DISTINCT target_id) c FROM events
           WHERE event_type='submit' AND target_id IN (SELECT id FROM targets WHERE campaign_id=?)""",
        (campaign_id,),
    ).fetchone()["c"]

    def pct(n):
        return round((n / total * 100), 1) if total else 0.0

    return {
        "total": total,
        "sent": sent,
        "rejected": rejected,
        "opened": opened,
        "clicked": clicked,
        "submitted": submitted,
        "pct_sent": pct(sent),
        "pct_rejected": pct(rejected),
        "pct_opened": pct(opened),
        "pct_clicked": pct(clicked),
        "pct_submitted": pct(submitted),
    }


def per_user_log(db, campaign_id):
    """Journal détaillé par destinataire, avec la date/heure EXACTE de chaque action."""
    targets = db.execute("SELECT * FROM targets WHERE campaign_id=?", (campaign_id,)).fetchall()
    result = []
    for t in targets:
        events = db.execute(
            "SELECT * FROM events WHERE target_id=? ORDER BY created_at", (t["id"],)
        ).fetchall()

        opened_at = next((e["created_at"] for e in events if e["event_type"] == "open"), None)
        clicked_at = next((e["created_at"] for e in events if e["event_type"] == "click"), None)
        submitted_at = next((e["created_at"] for e in events if e["event_type"] == "submit"), None)

        last_action = "Aucune action"
        last_action_at = None
        if submitted_at:
            last_action, last_action_at = "A soumis le formulaire de sensibilisation", submitted_at
        elif clicked_at:
            last_action, last_action_at = "A cliqué sur le lien", clicked_at
        elif opened_at:
            last_action, last_action_at = "A ouvert l'email", opened_at
        elif t["sent_at"]:
            last_action, last_action_at = "Email envoyé, aucune interaction", t["sent_at"]

        result.append(
            {
                "email": t["email"],
                "first_name": t["first_name"],
                "last_name": t["last_name"],
                "department": t["department"],
                "status": t["status"],
                "sent_at": t["sent_at"],
                "sent_at_fmt": fmt_dt(t["sent_at"]),
                "opened": opened_at is not None,
                "opened_at": opened_at,
                "opened_at_fmt": fmt_dt(opened_at),
                "clicked": clicked_at is not None,
                "clicked_at": clicked_at,
                "clicked_at_fmt": fmt_dt(clicked_at),
                "submitted": submitted_at is not None,
                "submitted_at": submitted_at,
                "submitted_at_fmt": fmt_dt(submitted_at),
                "first_click_at": clicked_at,
                "last_action": last_action,
                "last_action_at_fmt": fmt_dt(last_action_at),
            }
        )
    return result


def lifetime_sent_count(db, user_id):
    """Nombre total d'emails déjà envoyés par ce compte, toutes organisations et
    campagnes confondues (utilisé pour le quota cumulé de l'offre gratuite)."""
    row = db.execute(
        """SELECT COUNT(*) c FROM targets
           WHERE status='sent' AND campaign_id IN (SELECT id FROM campaigns WHERE user_id=?)""",
        (user_id,),
    ).fetchone()
    return row["c"] if row else 0


# ---------------------------------------------------------------------------
# Sociétés abonnées / licences
# ---------------------------------------------------------------------------
def generate_license_key():
    import secrets as _secrets
    groups = ["".join(_secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(4)) for _ in range(4)]
    return "SMPH-" + "-".join(groups)


def company_seat_count(db, company_id):
    row = db.execute("SELECT COUNT(*) c FROM users WHERE company_id=?", (company_id,)).fetchone()
    return row["c"] if row else 0


def company_license_active(company):
    """True si la licence Pro de cette société est en cours de validité (non expirée,
    non révoquée). Une société sans licence (offre gratuite) renvoie False ici."""
    if not company:
        return False
    if company["status"] != "active":
        return False
    if company["license_plan"] != "pro":
        return False
    if not company["license_expires_at"]:
        return False
    return datetime.utcnow().isoformat() <= company["license_expires_at"]


def effective_plan(db, user):
    """Détermine l'offre effective d'un utilisateur : Pro si sa société a une licence
    valide en cours, sinon essai gratuit."""
    if not user["company_id"]:
        return "free"
    company = db.execute("SELECT * FROM companies WHERE id=?", (user["company_id"],)).fetchone()
    return "pro" if company_license_active(company) else "free"


# ---------------------------------------------------------------------------
# Piste d'audit des connexions
# ---------------------------------------------------------------------------
def log_login_attempt(db, user_id, email_attempted, success, req):
    db.execute(
        """INSERT INTO login_audit (user_id, email_attempted, success, ip_address, user_agent, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            user_id, email_attempted, 1 if success else 0,
            req.remote_addr, req.headers.get("User-Agent", ""),
            datetime.utcnow().isoformat(),
        ),
    )
    db.commit()


# ---------------------------------------------------------------------------
# Sessions concurrentes (max 2 par compte)
# ---------------------------------------------------------------------------
MAX_CONCURRENT_SESSIONS = 2


def create_session(db, user_id, session_token, req):
    now = datetime.utcnow().isoformat()
    db.execute(
        """INSERT INTO user_sessions (user_id, session_token, created_at, last_seen_at, ip_address, user_agent, revoked)
           VALUES (?, ?, ?, ?, ?, ?, 0)""",
        (user_id, session_token, now, now, req.remote_addr, req.headers.get("User-Agent", "")),
    )
    db.commit()

    active = db.execute(
        """SELECT id FROM user_sessions WHERE user_id=? AND revoked=0 ORDER BY last_seen_at ASC""",
        (user_id,),
    ).fetchall()
    if len(active) > MAX_CONCURRENT_SESSIONS:
        to_revoke = active[: len(active) - MAX_CONCURRENT_SESSIONS]
        for row in to_revoke:
            db.execute("UPDATE user_sessions SET revoked=1 WHERE id=?", (row["id"],))
        db.commit()


def touch_session(db, session_token):
    db.execute(
        "UPDATE user_sessions SET last_seen_at=? WHERE session_token=? AND revoked=0",
        (datetime.utcnow().isoformat(), session_token),
    )
    db.commit()


def is_session_valid(db, session_token):
    row = db.execute(
        "SELECT id FROM user_sessions WHERE session_token=? AND revoked=0", (session_token,)
    ).fetchone()
    return row is not None
