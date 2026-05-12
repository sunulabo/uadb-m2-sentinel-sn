import json
import time
import random
import sys
import os
import hashlib
from datetime import datetime
from kafka import KafkaProducer
import pandas as pd

# Ajouter le répertoire parent au PYTHONPATH pour importer data_models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_models.schema import validate_data

# Configuration du Producer
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

TOPIC_NAME = 'equipe02_sentinel_data'
REGIONS = ["Dakar", "Saint-Louis", "Ziguinchor", "Touba", "Thies"]
PATHOLOGIES = ["PALU", "GRIPPE", "DENGUE", "CHOLERA"]

def generate_health_data():
    raw_id = f"P-{random.randint(1000, 9999)}"
    # Privacy Layer : Hachage de l'identifiant pour garantir l'anonymat
    hashed_id = hashlib.sha256(raw_id.encode('utf-8')).hexdigest()
    
    return {
        "id_patient": hashed_id,
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
        
        # Validation avec Pandera (via data_models.schema)
        df = pd.DataFrame([data])
        
        # Le modèle convertit 'date_consultation' en Timestamp, on garde les données originales pour l'envoi JSON
        validated_df = validate_data(df)
        
        if validated_df is not None:
            # Si valide, on envoie le message (les données originales en dict pour la sérialisation JSON)
            producer.send(TOPIC_NAME, data)
            print(f"✅ Donnée valide et envoyée : {data}")
        else:
            print(f"❌ Donnée invalide rejetée : {data}")
            
        time.sleep(2)  # Pause de 2 secondes entre chaque envoi
except KeyboardInterrupt:
    print("Simulateur arrêté.")
finally:
    producer.close()
