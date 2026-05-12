# insert_test_data.py — Insertion données de test dans HBase
# Équipe 02 | FALL Ahmed | UADB 2025-2026
# Données réalistes : ROUGE / ORANGE / VERT par district

import happybase
import random
from datetime import date

DISTRICTS = {
    '1': 'Dakar',       '2': 'Pikine',
    '3': 'Thiès',       '4': 'Kaolack',
    '5': 'Ziguinchor',  '6': 'Saint-Louis',
    '7': 'Tambacounda', '8': 'Diourbel'
}
MALADIES = ['PALUD', 'DENGUE', 'CHOLERA', 'TYPHOIDE']

# ── Règles de génération par district/maladie ──────────────
# ROUGE  : nb_cas > 80  (seuil critique)
# ORANGE : nb_cas 40-65 (surveillance)
# VERT   : nb_cas < 30  (normal)

def generer_nb_cas(district_id: str, maladie: str, jour: int) -> int:
    """Génère un nombre de cas réaliste selon le district et la maladie."""

    # ── Districts ROUGE ────────────────────────────────────
    # Dakar : forte densité → PALUD critique
    if district_id == '1' and maladie == 'PALUD':
        return random.randint(90, 150)

    # Ziguinchor : zone humide → CHOLERA critique
    if district_id == '5' and maladie == 'CHOLERA':
        return random.randint(85, 130)

    # Saint-Louis : zone fluviale → TYPHOIDE critique
    if district_id == '6' and maladie == 'TYPHOIDE':
        return random.randint(88, 120)

    # ── Districts ORANGE ───────────────────────────────────
    # Pikine : densité moyenne → DENGUE surveillance
    if district_id == '2' and maladie == 'DENGUE':
        return random.randint(45, 65)

    # Thiès : ville moyenne → PALUD surveillance
    if district_id == '3' and maladie == 'PALUD':
        return random.randint(42, 60)

    # Kaolack : chaleur → TYPHOIDE surveillance
    if district_id == '4' and maladie == 'TYPHOIDE':
        return random.randint(40, 58)

    # ── Districts VERT ─────────────────────────────────────
    # Tambacounda et Diourbel : zones moins denses → normal
    if district_id in ['7', '8']:
        return random.randint(5, 25)

    # Cas récents (derniers 10 jours) → moins de cas
    if jour >= 20:
        return random.randint(1, 20)

    # ── Cas par défaut ─────────────────────────────────────
    return random.randint(10, 50)


# ── Connexion HBase ────────────────────────────────────────
print('Connexion à HBase...')
conn = happybase.Connection('localhost', port=9090, timeout=60000)
conn.open()

tables_existantes = [t.decode() for t in conn.tables()]
print(f'Tables existantes : {tables_existantes}')

if 'epidemio:cas' not in tables_existantes:
    print('Table epidemio:cas introuvable — lance hbase_setup.py d\'abord')
    conn.close()
    exit(1)

table = conn.table(b'epidemio:cas')

# ── Insertion ──────────────────────────────────────────────
compteur   = 0
nb_rouge   = 0
nb_orange  = 0
nb_vert    = 0

for district_id, district_nom in DISTRICTS.items():
    for maladie in MALADIES:
        for jour in range(30):
            nb_cas = generer_nb_cas(district_id, maladie, jour)

            # Calculer le statut pour l'affichage
            if nb_cas > 80:
                statut = 'ROUGE'
                nb_rouge += 1
            elif nb_cas > 40:
                statut = 'ORANGE'
                nb_orange += 1
            else:
                statut = 'VERT'
                nb_vert += 1

            row_key = f'{district_id}_{maladie}_{jour}'.encode()

            try:
                table.put(row_key, {
                    b'info:district_id':     district_id.encode(),
                    b'info:district_nom':    district_nom.encode(),
                    b'info:maladie_code':    maladie.encode(),
                    b'stats:nombre_cas':     str(nb_cas).encode(),
                    b'stats:taux_incidence': str(round(nb_cas / 1000, 4)).encode(),
                    b'alerte:statut':        statut.encode(),
                    b'alerte:date':          str(date.today()).encode(),
                })
                compteur += 1

            except Exception as e:
                print(f'Erreur ligne {row_key.decode()} : {e}')
                continue

    print(f'  ✓ {district_nom} inséré')

conn.close()

# ── Résumé ─────────────────────────────────────────────────
print('\n' + '='*45)
print('  Insertion terminée — Sentinel-SN Équipe 02')
print('='*45)
print(f'  Total inséré : {compteur} enregistrements')
print(f'  ROUGE        : {nb_rouge}')
print(f'  ORANGE       : {nb_orange}')
print(f'  VERT         : {nb_vert}')
print('='*45)