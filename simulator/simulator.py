import json
import random
import time
from faker import Faker
from kafka import KafkaProducer

fake = Faker('fr_FR')

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

event_types = [
    'NOUVELLE_VENTE',
    'PAIEMENT',
    'ENTRETIEN_SAV',
    'ACCIDENT',
    'LOCATION_LCD',
    'LOCATION_LLD',
    'FIN_LOCATION',
    'OPPORTUNITE',
    'NOUVEAU_CLIENT',
]

def generate_event():
    event_type = random.choice(event_types)
    event = {
        "event_type": event_type,
        "client_id":  random.randint(1, 500),
        "car_id":     random.randint(1, 100),
        "amount":     round(random.uniform(200, 8000), 2),
        "status":     random.choice(['active', 'completed', 'cancelled']),
        "timestamp":  time.time()
    }
    if event_type in ['LOCATION_LCD', 'LOCATION_LLD']:
        event['rpd']           = round(random.uniform(150, 600), 2)
        event['return_on_time'] = random.choice([True, False])
    return event

print("Simulateur demarre ! Envoi des evenements...")

while True:
    event = generate_event()
    producer.send('tetouan_auto_events', event)
    print(f"Envoye : {event['event_type']} — client {event['client_id']}")
    time.sleep(5)