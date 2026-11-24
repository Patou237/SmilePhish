"""
Planificateur d'envois en arrière-plan pour SmilePhish.

Fonctionnement : un thread tourne en continu tant que le processus app.py est en vie,
et vérifie périodiquement s'il existe des campagnes planifiées dont la date/heure est
atteinte. Si oui, il lance l'envoi automatiquement avec les identifiants SMTP stockés
(chiffrés) au moment de la planification.

!! IMPORTANT !! Ce mécanisme ne fonctionne QUE si le processus serveur (python3 app.py)
reste en cours d'exécution jusqu'à la date planifiée — sur une machine qui reste allumée
et connectée (VM, petit serveur cloud, etc.), pas uniquement sur un poste personnel que
vous risquez d'éteindre. Si le serveur est arrêté au moment prévu, l'envoi planifié ne
partira pas tant que le serveur n'aura pas redémarré (il sera alors détecté en retard et
envoyé dès le redémarrage, sauf s'il a été annulé entre-temps).
"""

import threading
import time
from datetime import datetime, timezone

import db as dbmod
import mailer
import plans

CHECK_INTERVAL_SECONDS = 20

_thread = None
_stop_flag = False


def _run_due_campaign(conn, campaign, public_base_url):
    import crypto_utils

    campaign_id = campaign["id"]

    if campaign["admin_status"] == "suspended":
        conn.execute(
            "UPDATE campaigns SET schedule_status='failed', schedule_error=? WHERE id=?",
            ("Envoi annulé : campagne suspendue par l'administration de la plateforme.", campaign_id),
        )
        conn.commit()
        return

    try:
        smtp_pass = crypto_utils.decrypt(campaign["smtp_pass_enc"])
    except Exception as e:
        conn.execute(
            "UPDATE campaigns SET schedule_status='failed', schedule_error=? WHERE id=?",
            (f"Déchiffrement du mot de passe impossible : {e}", campaign_id),
        )
        conn.commit()
        return

    smtp_params = {
        "smtp_host": campaign["smtp_host"],
        "smtp_port": campaign["smtp_port"],
        "smtp_user": campaign["smtp_user"],
        "smtp_pass": smtp_pass,
        "use_tls": bool(campaign["smtp_use_tls"]),
        "delay_ms": campaign["smtp_delay_ms"],
    }

    # Quota de l'offre en cours, revérifié au moment de l'envoi (il peut avoir changé
    # depuis la planification : autres campagnes envoyées entretemps, changement d'offre).
    user = conn.execute("SELECT * FROM users WHERE id=?", (campaign["user_id"],)).fetchone()
    plan = dbmod.effective_plan(conn, user) if user else "free"
    max_lifetime = plans.max_lifetime_sent(plan)
    targets = conn.execute(
        "SELECT * FROM targets WHERE campaign_id=? AND status='pending'", (campaign_id,)
    ).fetchall()

    max_targets = plans.max_targets_per_campaign(plan)
    if max_lifetime is not None:
        already_sent = dbmod.lifetime_sent_count(conn, campaign["user_id"])
        remaining = max(0, max_lifetime - already_sent)
        max_targets = min(max_targets, remaining)

    try:
        sent, rejected, errors = mailer.send_batch(
            conn, campaign, targets, smtp_params, public_base_url, max_targets=max_targets
        )
        status = "sent"
        error_summary = None
        if errors:
            error_summary = " | ".join(errors[:5])
        if max_targets < len(targets):
            note = (
                f"Quota de l'offre atteint : seuls {max_targets} sur {len(targets)} "
                f"destinataires ont été envoyés."
            )
            error_summary = f"{error_summary} | {note}" if error_summary else note
        conn.execute(
            "UPDATE campaigns SET schedule_status=?, schedule_error=? WHERE id=?",
            (status, error_summary, campaign_id),
        )
    except Exception as e:
        conn.execute(
            "UPDATE campaigns SET schedule_status='failed', schedule_error=? WHERE id=?",
            (str(e), campaign_id),
        )
    conn.commit()


def _loop(public_base_url):
    while not _stop_flag:
        try:
            conn = dbmod.connect()
            try:
                now_iso = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
                due = conn.execute(
                    """SELECT * FROM campaigns
                       WHERE schedule_status='scheduled' AND scheduled_at IS NOT NULL
                         AND scheduled_at <= ?""",
                    (now_iso,),
                ).fetchall()
                for campaign in due:
                    _run_due_campaign(conn, campaign, public_base_url)
            finally:
                conn.close()
        except Exception:
            # Ne jamais laisser une erreur inattendue arrêter le thread de fond.
            pass
        time.sleep(CHECK_INTERVAL_SECONDS)


def start(public_base_url):
    global _thread, _stop_flag
    if _thread and _thread.is_alive():
        return
    _stop_flag = False
    _thread = threading.Thread(target=_loop, args=(public_base_url,), daemon=True)
    _thread.start()


def stop():
    global _stop_flag
    _stop_flag = True
