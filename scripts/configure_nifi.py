"""
configure_nifi.py — Configuration automatique du flux NiFi 1.27 (Sentinel-SN, Équipe 02)

Flux créé :
  ConsumeKafkaRecord_2_6 → UpdateAttribute → ConvertRecord (JSON→Parquet) → PutHDFS

Usage :
  # Attendre que NiFi soit UP (~90 secondes après docker compose up)
  source .venv/bin/activate
  python scripts/configure_nifi.py

Prérequis :
  - NiFi 1.27 sur https://localhost:8443
  - Kafka sur localhost:9092
  - HDFS NameNode sur hdfs://namenode:9000
"""

import requests
import json
import sys
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NIFI_BASE  = "https://localhost:8443/nifi-api"
USERNAME   = "admin"
PASSWORD   = "sentinel_password_2026"
KAFKA_HOST = "kafka:9092"          # nom de service Docker interne
TOPIC      = "equipe02_sentinel_data"
HDFS_URI   = "hdfs://namenode:9000"


# ─── Auth ─────────────────────────────────────────────────────────────────────
def get_token() -> str:
    resp = requests.post(
        f"{NIFI_BASE}/access/token",
        data={"username": USERNAME, "password": PASSWORD},
        verify=False
    )
    resp.raise_for_status()
    print("✅ Authentification NiFi réussie.")
    return resp.text.strip()


def h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ─── Root Process Group ───────────────────────────────────────────────────────
def get_root_pg(token: str) -> dict:
    r = requests.get(f"{NIFI_BASE}/flow/process-groups/root", headers=h(token), verify=False)
    r.raise_for_status()
    pg = r.json()["processGroupFlow"]
    print(f"✅ Process Group racine : {pg['id']}")
    return pg


def get_revision(token: str) -> dict:
    """Récupère la révision du composant racine pour les mises à jour."""
    return {"version": 0, "clientId": "sentinel-config-script"}


# ─── Controller Services (JsonTreeReader + ParquetRecordSetWriter) ────────────
def create_controller_service(token: str, pg_id: str, cs_type: str, name: str, props: dict) -> str:
    payload = {
        "revision": {"version": 0},
        "component": {"type": cs_type, "name": name, "properties": props}
    }
    r = requests.post(
        f"{NIFI_BASE}/process-groups/{pg_id}/controller-services",
        headers=h(token), json=payload, verify=False
    )
    if r.status_code not in (200, 201):
        print(f"  ⚠️  Controller Service '{name}' : {r.status_code} — {r.text[:300]}")
        return None
    cs_id = r.json()["id"]
    # Activer le Controller Service
    enable_payload = {"revision": {"version": 1}, "component": {"id": cs_id, "state": "ENABLED"}}
    requests.put(f"{NIFI_BASE}/controller-services/{cs_id}/run-status",
                 headers=h(token), json=enable_payload, verify=False)
    print(f"  ✅ Controller Service '{name}' créé et activé ({cs_id[:8]}...)")
    return cs_id


# ─── Processor ───────────────────────────────────────────────────────────────
def create_processor(token: str, pg_id: str, proc_type: str, name: str,
                     x: int, y: int, props: dict = {}, auto_term: list = []) -> str:
    payload = {
        "revision": {"version": 0},
        "component": {
            "type": proc_type,
            "name": name,
            "position": {"x": x, "y": y},
            "config": {
                "properties": props,
                "autoTerminatedRelationships": auto_term
            }
        }
    }
    r = requests.post(
        f"{NIFI_BASE}/process-groups/{pg_id}/processors",
        headers=h(token), json=payload, verify=False
    )
    if r.status_code not in (200, 201):
        print(f"  ⚠️  Processor '{name}' : {r.status_code} — {r.text[:300]}")
        return None
    proc_id = r.json()["id"]
    print(f"  ✅ Processor '{name}' créé ({proc_id[:8]}...)")
    return proc_id


# ─── Connexion ────────────────────────────────────────────────────────────────
def connect(token: str, pg_id: str, src_id: str, dst_id: str, rels: list) -> str:
    payload = {
        "revision": {"version": 0},
        "component": {
            "source": {"id": src_id, "groupId": pg_id, "type": "PROCESSOR"},
            "destination": {"id": dst_id, "groupId": pg_id, "type": "PROCESSOR"},
            "selectedRelationships": rels,
            "backPressureObjectThreshold": 10000,
            "backPressureDataSizeThreshold": "1 GB"
        }
    }
    r = requests.post(
        f"{NIFI_BASE}/process-groups/{pg_id}/connections",
        headers=h(token), json=payload, verify=False
    )
    if r.status_code not in (200, 201):
        print(f"  ⚠️  Connexion {src_id[:8]}→{dst_id[:8]} : {r.status_code}")
        return None
    print(f"  ✅ Connexion {rels} créée")
    return r.json()["id"]


# ─── Démarrage d'un processor ─────────────────────────────────────────────────
def start_processor(token: str, proc_id: str, name: str):
    payload = {"revision": {"version": 1}, "component": {"id": proc_id, "state": "RUNNING"}}
    r = requests.put(
        f"{NIFI_BASE}/processors/{proc_id}/run-status",
        headers=h(token), json=payload, verify=False
    )
    if r.status_code in (200, 202):
        print(f"  ▶️  Processor '{name}' démarré")
    else:
        print(f"  ⚠️  Démarrage '{name}' : {r.status_code} (configurer manuellement si besoin)")


# ─── Programme principal ──────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Sentinel-SN — Configuration NiFi 1.27 (Kafka → HDFS)")
    print("=" * 60)

    # Attendre que NiFi soit prêt
    print("\n⏳ Vérification que NiFi est prêt...")
    for i in range(20):
        try:
            r = requests.get(f"{NIFI_BASE}/access/config", verify=False, timeout=5)
            if r.status_code in (200, 401):
                print(f"✅ NiFi est prêt")
                break
        except Exception:
            pass
        print(f"   Tentative {i+1}/20... (NiFi démarre, attente 10s)")
        time.sleep(10)
    else:
        print("❌ NiFi inaccessible après 200s. Vérifiez : docker ps")
        sys.exit(1)

    token = get_token()
    pg    = get_root_pg(token)
    pg_id = pg["id"]

    # Vérification flux existant
    existing = pg["flow"]["processors"]
    if existing:
        print(f"\n⚠️  {len(existing)} processor(s) déjà présents — flux existant détecté.")
        print("   Supprimez-les via https://localhost:8443/nifi si vous souhaitez reconfigurer.")
        sys.exit(0)

    # ── 1. Controller Services ────────────────────────────────────────────────
    print("\n[1/5] Création des Controller Services...")

    reader_id = create_controller_service(
        token, pg_id,
        cs_type="org.apache.nifi.json.JsonTreeReader",
        name="JsonTreeReader — Sentinel",
        props={"schema-access-strategy": "infer-schema"}
    )

    parquet_writer_id = create_controller_service(
        token, pg_id,
        cs_type="org.apache.nifi.parquet.ParquetRecordSetWriter",
        name="ParquetRecordSetWriter — Sentinel",
        props={
            "schema-access-strategy": "inherit-record-schema",
            "compression-type": "SNAPPY"
        }
    )

    time.sleep(2)  # Laisser le temps aux CS de s'activer

    # ── 2. ConsumeKafkaRecord ─────────────────────────────────────────────────
    print("\n[2/5] Création du processor ConsumeKafkaRecord...")
    kafka_id = create_processor(
        token, pg_id,
        proc_type="org.apache.nifi.processors.kafka.pubsub.ConsumeKafkaRecord_2_6",
        name="ConsumeKafka — equipe02_sentinel_data",
        x=0, y=0,
        props={
            "bootstrap.servers": KAFKA_HOST,
            "topic": TOPIC,
            "group.id": "equipe02_nifi_consumer",
            "auto.offset.reset": "earliest",
            "key-record-reader": reader_id,
            "record-writer": reader_id,
        }
    )

    # ── 3. UpdateAttribute — enrichissement partition HDFS ───────────────────
    print("\n[3/5] Création du processor UpdateAttribute...")
    update_id = create_processor(
        token, pg_id,
        proc_type="org.apache.nifi.processors.attributes.UpdateAttribute",
        name="UpdateAttribute — Partitionnement HDFS",
        x=400, y=0,
        props={
            "annee":     "${now():format('yyyy')}",
            "mois":      "${now():format('MM')}",
            "hdfs.path": f"/user/equipe02/sentinel_data/analytics/"
                         f"annee=${{annee}}/mois=${{mois}}/region=${{region}}/"
        }
    )

    # ── 4. ConvertRecord (JSON → Parquet) ─────────────────────────────────────
    print("\n[4/5] Création du processor ConvertRecord (JSON → Parquet)...")
    convert_id = create_processor(
        token, pg_id,
        proc_type="org.apache.nifi.processors.standard.ConvertRecord",
        name="ConvertRecord — JSON to Parquet",
        x=800, y=0,
        props={
            "record-reader": reader_id,
            "record-writer": parquet_writer_id,
        },
        auto_term=["failure"]
    )

    # ── 5. PutHDFS ────────────────────────────────────────────────────────────
    print("\n[5/5] Création du processor PutHDFS...")
    hdfs_id = create_processor(
        token, pg_id,
        proc_type="org.apache.nifi.processors.hadoop.PutHDFS",
        name="PutHDFS — equipe02/sentinel_analytics",
        x=1200, y=0,
        props={
            "Hadoop Configuration Resources": "/etc/hadoop/conf/core-site.xml",
            "fs.defaultFS": HDFS_URI,
            "Directory": "${hdfs.path}",
            "Conflict Resolution Strategy": "replace",
            "Compression codec": "org.apache.hadoop.io.compress.SnappyCodec",
            "Block Size": "134217728",  # 128 MB
        },
        auto_term=["failure", "success"]
    )

    # ── Connexions ────────────────────────────────────────────────────────────
    print("\nCréation des connexions...")
    if kafka_id and update_id:
        connect(token, pg_id, kafka_id, update_id, ["success"])
    if update_id and convert_id:
        connect(token, pg_id, update_id, convert_id, ["success"])
    if convert_id and hdfs_id:
        connect(token, pg_id, convert_id, hdfs_id, ["success"])

    # ── Démarrage des processors ──────────────────────────────────────────────
    print("\nDémarrage des processors...")
    time.sleep(2)
    for proc_id, name in [
        (kafka_id, "ConsumeKafka"),
        (update_id, "UpdateAttribute"),
        (convert_id, "ConvertRecord"),
        (hdfs_id, "PutHDFS"),
    ]:
        if proc_id:
            start_processor(token, proc_id, name)

    print()
    print("=" * 60)
    print("✅ Flux NiFi configuré et démarré !")
    print(f"   Interface : https://localhost:8443/nifi")
    print(f"   Interface HDFS : http://localhost:9870")
    print()
    print("📂 Structure HDFS écrite par NiFi :")
    print("   /user/equipe02/sentinel_data/analytics/")
    print("   └── annee=2026/mois=05/region=Dakar/*.parquet")
    print("=" * 60)


if __name__ == "__main__":
    main()
