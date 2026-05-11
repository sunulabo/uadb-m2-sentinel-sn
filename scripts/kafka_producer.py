import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

# Configuration du Producer
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

TOPIC_NAME = 'equipe02_sentinel_data'
REGIONS = ["Dakar", "Saint-Louis", "Ziguinchor", "Touba", "Thies"]
PATHOLOGIES = ["PALU", "GRIPPE", "DENGUE", "CHOLERA"]

def generate_health_data():
    return {
        "id_patient": f"P-{random.randint(1000, 9999)}",
        "date_consultation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "age": random.randint(1, 85),
        "sexe": random.choice(["M", "F"]),
        "code_pathologie": random.choice(PATHOLOGIES),
        "region": random.choice(REGIONS),
        "temperature": round(random.uniform(36.5, 40.5), 1)
    }

print(f"Démarrage du simulateur sur le topic : {TOPIC_NAME}")

try:
    while True:
        data = generate_health_data()
        producer.send(TOPIC_NAME, data)
        print(f"Donnée envoyée : {data}")
        time.sleep(2)  # Pause de 2 secondes entre chaque envoi
except KeyboardInterrupt:
    print("Simulateur arrêté.")
finally:
    producer.close()
