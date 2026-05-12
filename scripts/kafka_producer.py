"""
kafka_producer.py — Simulateur de données épidémiologiques (Sentinel-SN, Équipe 02)

Pipeline local :
  1. Génération de données synthétiques
  2. Anonymisation HMAC-SHA256 de l'ID patient (Privacy Layer)
  3. Validation Pandera avant envoi
  4. Publication sur le topic Kafka : equipe02_sentinel_data

Usage :
  export SENTINEL_HMAC_KEY="votre_cle_secrete"
  source .venv/bin/activate
  python scripts/kafka_producer.py
"""

import json
import time
import random
import sys
import os
import hmac
import hashlib
from datetime import datetime
from kafka import KafkaProducer
import pandas as pd

# Ajouter le répertoire parent au PYTHONPATH pour importer data_models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_models.schema import validate_data, REGIONS_VALIDES, PATHOLOGIES_VALIDES

# ─── Privacy Layer ────────────────────────────────────────────────────────────
# La clé secrète DOIT être définie en variable d'environnement en production.
# Valeur par défaut pour le développement uniquement.
_HMAC_KEY = os.environ.get("SENTINEL_HMAC_KEY", "sentinel_dev_key_equipe02").encode("utf-8")


def anonymize_id(raw_id: str) -> str:
    """Anonymise un identifiant patient par HMAC-SHA256.

    Contrairement à un simple SHA-256, le HMAC utilise une clé secrète,
    rendant les attaques par rainbow table impossibles sans la clé.

    Args:
        raw_id (str): Identifiant brut (ex: "P-1234").

    Returns:
        str: Hash HMAC-SHA256 hexadécimal (64 caractères).
    """
    return hmac.new(_HMAC_KEY, raw_id.encode("utf-8"), hashlib.sha256).hexdigest()


# ─── Configuration Kafka ─────────────────────────────────────────────────────
producer = KafkaProducer(
    bootstrap_servers=["localhost:9092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

TOPIC_NAME = "equipe02_sentinel_data"


def generate_health_data() -> dict:
    """Génère un enregistrement de santé synthétique anonymisé.

    Returns:
        dict: Données épidémiologiques avec ID patient haché.
    """
    raw_id = f"P-{random.randint(1000, 9999)}"

    return {
        "id_patient": anonymize_id(raw_id),              # ← HMAC-SHA256 (64 chars)
        "date_consultation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "age": random.randint(1, 85),
        "sexe": random.choice(["M", "F"]),
        "code_pathologie": random.choice(PATHOLOGIES_VALIDES),  # ← liste blanche
        "region": random.choice(REGIONS_VALIDES),               # ← liste blanche
        "temperature": round(random.uniform(36.5, 40.5), 1)
    }


# ─── Boucle principale ────────────────────────────────────────────────────────
print(f"Démarrage du simulateur → topic : {TOPIC_NAME}")
print(f"Privacy Layer : HMAC-SHA256 (clé {'env' if 'SENTINEL_HMAC_KEY' in os.environ else 'dev défaut'})")
print("-" * 55)

try:
    while True:
        data = generate_health_data()
        df = pd.DataFrame([data])

        validated_df = validate_data(df)

        if validated_df is not None:
            producer.send(TOPIC_NAME, data)
            print(f"✅ Envoyé | region={data['region']:<14} | patho={data['code_pathologie']:<8} | "
                  f"age={data['age']:>3} | temp={data['temperature']}°C")
        else:
            print(f"❌ Rejeté : {data}")

        time.sleep(2)

except KeyboardInterrupt:
    print("\nSimulateur arrêté proprement.")
finally:
    producer.close()
