from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

sid = os.getenv("TWILIO_ACCOUNT_SID")
token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("TWILIO_PHONE_NUMBER")
to_number = os.getenv("NOTIFICATION_PHONE")

print("SID:", sid)
print("FROM:", from_number)
print("TO:", to_number)

client = Client(sid, token)

message = client.messages.create(
    body="✅ Test SMS Tetouan Auto",
    from_=from_number,
    to=to_number
)

print("✅ SMS envoyé ! SID:", message.sid)