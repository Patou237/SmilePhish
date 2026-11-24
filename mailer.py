"""
Logique d'envoi des emails, partagée entre :
- l'envoi manuel déclenché depuis le tableau de bord ("Envoyer maintenant")
- l'envoi automatique déclenché par le planificateur en arrière-plan (scheduler.py)
  pour les campagnes planifiées à l'avance.
"""

import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


TRANSPARENT_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154"
    "789c6300010000050001"
    "0d0a2db40000000049454e44ae426082"
)


def build_email(campaign, target, public_base_url):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = campaign["subject"]
    msg["From"] = f"{campaign['sender_name']} <{campaign['sender_email']}>"
    msg["To"] = target["email"]

    click_url = f"{public_base_url}/track/click/{target['token']}"
    pixel_url = f"{public_base_url}/track/open/{target['token']}.png"

    html = campaign["html_template"]
    html = html.replace("{{PRENOM}}", target["first_name"] or "")
    html = html.replace("{{NOM}}", target["last_name"] or "")
    html = html.replace("{{LIEN}}", click_url)
    html += f'<img src="{pixel_url}" width="1" height="1" style="display:none" alt="">'

    msg.attach(MIMEText(html, "html"))
    return msg


def send_batch(db, campaign, targets, smtp_params, public_base_url, max_targets=None):
    """Envoie `targets` (liste de sqlite3.Row) pour `campaign` via les paramètres SMTP
    fournis. Respecte un plafond `max_targets` optionnel (quota de l'offre en cours) :
    les cibles au-delà ne sont pas envoyées et restent 'pending'.
    Retourne (sent_count, rejected_count, errors)."""
    smtp_host = smtp_params["smtp_host"]
    smtp_port = int(smtp_params["smtp_port"])
    smtp_user = smtp_params["smtp_user"]
    smtp_pass = smtp_params["smtp_pass"]
    use_tls = bool(smtp_params.get("use_tls", True))
    try:
        delay_ms = max(0, int(smtp_params.get("delay_ms", 300)))
    except (TypeError, ValueError):
        delay_ms = 300

    if max_targets is not None:
        targets = list(targets)[:max_targets]

    sent_count = 0
    rejected_count = 0
    errors = []

    server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
    try:
        if use_tls:
            server.starttls()
        server.login(smtp_user, smtp_pass)

        for i, t in enumerate(targets):
            try:
                msg = build_email(campaign, t, public_base_url)
                server.sendmail(campaign["sender_email"], t["email"], msg.as_string())
                db.execute(
                    "UPDATE targets SET status='sent', sent_at=? WHERE id=?",
                    (datetime.utcnow().isoformat(), t["id"]),
                )
                sent_count += 1
            except Exception as e:
                db.execute("UPDATE targets SET status='rejected' WHERE id=?", (t["id"],))
                rejected_count += 1
                errors.append(f"{t['email']}: {e}")

            db.commit()
            if delay_ms and i < len(targets) - 1:
                time.sleep(delay_ms / 1000)
    finally:
        try:
            server.quit()
        except Exception:
            pass

    return sent_count, rejected_count, errors
