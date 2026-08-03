# api/notifications.py

import os

# ============================================================
# NOTIFICATION EMAIL (SendGrid)
# ============================================================

def send_email_alert(client_id: int, score: float, decision: str):
    """
    Envoie un email si score > 0.50
    """
    try:
        api_key = os.getenv("SENDGRID_API_KEY", "")
        if not api_key:
            print(f"[EMAIL] Config manquante — Client {client_id} Score {score:.2f}")
            return False

        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email="noreply@tetouanauto.ma",
            to_emails=os.getenv("NOTIFICATION_EMAIL", "manager@tetouanauto.ma"),
            subject=f"[ALERTE] Client {client_id} — Score {score:.2f}",
            html_content=f"""
                <h2>Alerte Tetouan Auto</h2>
                <p>Client ID : <b>{client_id}</b></p>
                <p>Score SVC : <b>{score:.2f}</b></p>
                <p>Decision  : <b>{decision}</b></p>
            """
        )

        sg = SendGridAPIClient(api_key)
        sg.send(message)
        print(f"[EMAIL] Envoye — Client {client_id}")
        return True

    except Exception as e:
        print(f"[EMAIL] Erreur : {e}")
        return False


# ============================================================
# NOTIFICATION SMS (Twilio)
# ============================================================

def send_sms_alert(client_id: int, score: float, decision: str):
    """
    Envoie un SMS si score > 0.75
    """
    try:
        sid   = os.getenv("TWILIO_ACCOUNT_SID", "")
        token = os.getenv("TWILIO_AUTH_TOKEN", "")

        if not sid or not token:
            print(f"[SMS] Config manquante — Client {client_id}")
            return False

        from twilio.rest import Client

        client = Client(sid, token)
        message = client.messages.create(
            body=(
                f"[TETOUAN AUTO] ALERTE CRITIQUE\n"
                f"Client {client_id}\n"
                f"Score: {score:.2f}\n"
                f"Decision: {decision}"
            ),
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=os.getenv("NOTIFICATION_PHONE")
        )

        print(f"[SMS] Envoye — Client {client_id} SID: {message.sid}")
        return True

    except Exception as e:
        print(f"[SMS] Erreur : {e}")
        return False


# ============================================================
# LOGIQUE PRINCIPALE
# ============================================================

def send_notification(client_id: int, score: float, decision: str):
    """
    Score > 0.75 → SMS + Email
    Score > 0.50 → Email seulement
    Score < 0.50 → Rien
    """
    if score >= 0.75:
        send_email_alert(client_id, score, decision)
        send_sms_alert(client_id, score, decision)

    elif score >= 0.50:
        send_email_alert(client_id, score, decision)