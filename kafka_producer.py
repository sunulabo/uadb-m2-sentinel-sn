# kafka_producer.py — Simulateur épidémio + météo
# Sentinel-SN | Groupe 02 | UADB 2025-2026

from kafka import KafkaProducer
import json
import random
import time
from datetime import date

# ── Configuration ──────────────────────────────────────────
KAFKA_BROKER    = 'localhost:29092'
TOPIC_EPIDEMIO  = 'equipe02_epidemio_raw'
TOPIC_METEO     = 'equipe02_meteo_raw'

DISTRICTS = {
    1: 'Dakar',       2: 'Pikine',
    3: 'Thiès',       4: 'Kaolack',
    5: 'Ziguinchor',  6: 'Saint-Louis',
    7: 'Tambacounda', 8: 'Diourbel'
}

MALADIES = ['PALUD', 'DENGUE', 'CHOLERA', 'TYPHOIDE']
SOURCES  = ['DISTRICT', 'HOPITAL', 'API']

# ── Génération des données ─────────────────────────────────

def maladie_ponderee(mois: int) -> str:
    """Paludisme dominant en hivernage sénégalais (juil-oct)."""
    if 7 <= mois <= 10:
        poids = [0.60, 0.20, 0.10, 0.10]
    else:
        poids = [0.30, 0.30, 0.20, 0.20]
    return random.choices(MALADIES, weights=poids, k=1)[0]


def pluviometrie(mois: int) -> float:
    """Modèle hivernage sénégalais — pic en août (200mm/mois)."""
    pluie_mensuelle = {
        1: 0,  2: 0,  3: 0,  4: 0,  5: 2,
        6: 15, 7: 80, 8: 200, 9: 150, 10: 40,
        11: 5, 12: 0
    }
    base = pluie_mensuelle.get(mois, 0) / 30
    return max(0.0, round(random.gauss(base, 2), 1))


def generer_cas(district_id: int, d: date) -> dict:
    """Génère un enregistrement de cas épidémiologique simulé."""
    cas   = random.randint(1, 80)
    deces = random.randint(0, max(1, cas // 20))
    return {
        'patient_raw_id':   f'SN{district_id:03d}{random.randint(100000, 999999)}',
        'district_id':      district_id,
        'district_nom':     DISTRICTS[district_id],
        'maladie_code':     maladie_ponderee(d.month),
        'nombre_cas':       cas,
        'nombre_deces':     deces,
        'date_declaration': str(d),
        'source_rapport':   random.choice(SOURCES)
    }


def generer_meteo(district_id: int, d: date) -> dict:
    """Génère des données météo simulées avec corrélation saisonnière."""
    pluie = pluviometrie(d.month)
    return {
        'district_id':     district_id,
        'district_nom':    DISTRICTS[district_id],
        'date_mesure':     str(d),
        'temperature_c':   round(random.uniform(22, 38), 1),
        'pluviometrie_mm': pluie,
        'humidite_pct':    round(min(100.0, 40 + pluie * 2 + random.gauss(0, 5)), 1)
    }

# ── Connexion Kafka ────────────────────────────────────────

def creer_producer() -> KafkaProducer:
    """Initialise le producteur Kafka avec sérialisation JSON."""
    return KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        key_serializer=lambda k: str(k).encode('utf-8'),
        retries=5,
        acks='all'
    )

# ── Boucle principale ──────────────────────────────────────

if __name__ == '__main__':
    print('=' * 50)
    print('  Sentinel-SN | Équipe 02 | FALL Ahmed')
    print(f'  Broker : {KAFKA_BROKER}')
    print(f'  Topics : {TOPIC_EPIDEMIO}')
    print(f'           {TOPIC_METEO}')
    print('=' * 50)

    producer = creer_producer()
    today    = date.today()
    batch    = 0

    try:
        while True:
            for district_id in DISTRICTS:
                # Envoi épidémiologique
                producer.send(
                    TOPIC_EPIDEMIO,
                    key=district_id,
                    value=generer_cas(district_id, today)
                )
                # Envoi météo
                producer.send(
                    TOPIC_METEO,
                    key=district_id,
                    value=generer_meteo(district_id, today)
                )

            producer.flush()
            batch += 1
            print(f'[S1][Batch {batch}] {today} — {len(DISTRICTS) * 2} messages envoyés')
            time.sleep(5)

    except KeyboardInterrupt:
        print('\nSimulateur arrêté.')
        producer.close()
