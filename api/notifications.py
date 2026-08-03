# api/notifications.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS    = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD   = os.getenv("GMAIL_APP_PASSWORD")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL")

def send_email_alert(client_id, score, alert_level, decision, segment):
    """
    Envoie un email d'alerte selon le niveau de risque
    """
    # Définir le sujet selon le niveau
    if alert_level == "CRITIQUE":
        subject  = f"🔴 URGENT — Client {client_id} va partir !"
        couleur  = "#dc3545"
        emoji    = "🔴"
    elif alert_level == "MODEREE":
        subject  = f"🟠 ATTENTION — Client {client_id} à risque"
        couleur  = "#fd7e14"
        emoji    = "🟠"
    else:
        return  # Pas d'email pour NORMAL

    # Corps de l'email en HTML
    body = f"""
    <html>
    <body style="font-family: Arial; padding: 20px;">

        <div style="background-color: {couleur};
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;">
            <h2>{emoji} ALERTE CHURN — Tétouan Automobile</h2>
        </div>

        <table style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <b>Client ID</b>
                </td>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    {client_id}
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <b>Score SVC</b>
                </td>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    {score:.2f} / 1.00
                </td>
            </tr>
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <b>Niveau d'alerte</b>
                </td>
                <td style="padding: 10px;
                           border: 1px solid #ddd;
                           color: {couleur};
                           font-weight: bold;">
                    {emoji} {alert_level}
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <b>Segment client</b>
                </td>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    {segment}
                </td>
            </tr>
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <b>Action recommandée</b>
                </td>
                <td style="padding: 10px;
                           border: 1px solid #ddd;
                           font-weight: bold;">
                    {decision}
                </td>
            </tr>
        </table>

        <div style="background-color: #e8f4fd;
                    padding: 15px;
                    border-radius: 8px;
                    margin-top: 20px;">
            <p><b>Action immédiate requise :</b></p>
            <p>Contactez ce client dès que possible
               pour éviter de le perdre !</p>
        </div>

        <p style="color: #666; font-size: 12px; margin-top: 20px;">
            Système Intelligence Commerciale —
            Tétouan Automobile — RentopCar
        </p>

    </body>
    </html>
    """

    # Créer le message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = GMAIL_ADDRESS
    msg['To']      = NOTIFICATION_EMAIL

    msg.attach(MIMEText(body, 'html'))

    # Envoyer via Gmail SMTP
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Email envoye : {subject}")
        return True
    except Exception as e:
        print(f"Erreur email : {e}")
        return False


def send_notification(client_id, score, alert_level, decision, segment):
    """
    Fonction principale qui gere toutes les notifications
    Score > 0.75 → Email CRITIQUE
    Score > 0.50 → Email MODEREE
    Score < 0.50 → Rien (juste Grafana)
    """
    if alert_level in ["CRITIQUE", "MODEREE"]:
        send_email_alert(
            client_id=client_id,
            score=score,
            alert_level=alert_level,
            decision=decision,
            segment=segment
        )


if __name__ == "__main__":
    # Test direct
    print("Test notification Gmail...")
    send_email_alert(
        client_id=42,
        score=0.85,
        alert_level="CRITIQUE",
        decision="RELANCER",
        segment="VIP"
    )