# privacy_layer.py — Privacy Layer Sentinel-SN
# Équipe 02 | FALL Ahmed | UADB 2025-2026
# Anonymisation des données patient par hachage SHA-256 + sel

import hashlib
import os
import logging
import pandas as pd

logger = logging.getLogger('PrivacyLayer')

# ── Sel secret (jamais en dur en production) ───────────────
SALT = os.environ.get('SENTINEL_SALT', 'equipe02_sentinel_salt_2025')

# ── Champs PII à supprimer absolument ─────────────────────
PII_FIELDS = [
    'patient_raw_id',   # identifiant brut du patient
    'nom',              # nom si présent
    'prenom',           # prénom si présent
    'telephone',        # téléphone si présent
    'adresse'           # adresse si présente
]

# ── Fonctions principales ──────────────────────────────────

def hacher_identifiant(raw_id: str) -> str:
    """
    Hash SHA-256 avec sel de l'identifiant brut du patient.
    Le résultat est irréversible — impossible de retrouver raw_id.
    """
    valeur = f"{raw_id}{SALT}"
    return hashlib.sha256(valeur.encode('utf-8')).hexdigest()


def anonymiser_message(message: dict) -> dict:
    """
    Anonymise un message épidémiologique :
    1. Hache patient_raw_id → patient_id_secure
    2. Supprime tous les champs PII
    Retourne le message nettoyé.
    """
    message_secure = message.copy()

    # Hacher l'identifiant brut s'il existe
    if 'patient_raw_id' in message_secure:
        message_secure['patient_id_secure'] = hacher_identifiant(
            message_secure['patient_raw_id']
        )
        logger.debug(f"PII haché : {message_secure['patient_raw_id'][:6]}*** → {message_secure['patient_id_secure'][:12]}...")

    # Supprimer tous les champs PII
    for champ in PII_FIELDS:
        if champ in message_secure:
            del message_secure[champ]
            logger.info(f"Champ PII supprimé : {champ}")

    return message_secure


def verifier_absence_pii(message: dict) -> bool:
    """
    Vérifie qu'aucun champ PII n'est présent dans le message.
    Retourne True si le message est propre, False sinon.
    """
    fuites = [champ for champ in PII_FIELDS if champ in message]

    if fuites:
        logger.error(f"FUITE PII DÉTECTÉE — champs trouvés : {fuites}")
        return False

    logger.info("Vérification PII : OK — aucune donnée nominative détectée")
    return True


def anonymiser_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Anonymise un DataFrame pandas complet.
    Utilisé pour les tests et l'analyse batch.
    """
    df = df.copy()

    if 'patient_raw_id' in df.columns:
        df['patient_id_secure'] = df['patient_raw_id'].apply(hacher_identifiant)

    # Supprimer toutes les colonnes PII présentes
    colonnes_a_supprimer = [c for c in PII_FIELDS if c in df.columns]
    df.drop(columns=colonnes_a_supprimer, inplace=True)

    logger.info(f"DataFrame anonymisé — {len(colonnes_a_supprimer)} colonne(s) PII supprimée(s)")
    return df


# ── Test rapide ────────────────────────────────────────────

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Simuler un message brut venant de Kafka
    message_brut = {
        'patient_raw_id':   'SN001123456',
        'district_id':      1,
        'district_nom':     'Dakar',
        'maladie_code':     'PALUD',
        'nombre_cas':       15,
        'nombre_deces':     1,
        'date_declaration': '2025-08-15',
        'source_rapport':   'HOPITAL'
    }

    print("\n── Message AVANT anonymisation ──")
    for k, v in message_brut.items():
        print(f"  {k}: {v}")

    message_secure = anonymiser_message(message_brut)

    print("\n── Message APRÈS anonymisation ──")
    for k, v in message_secure.items():
        print(f"  {k}: {v}")

    print("\n── Vérification absence PII ──")
    propre = verifier_absence_pii(message_secure)
    print(f"  Résultat : {'✓ PROPRE' if propre else '✗ FUITE DÉTECTÉE'}")

    # Vérifier que le hash est stable (même entrée = même hash)
    hash1 = hacher_identifiant('SN001123456')
    hash2 = hacher_identifiant('SN001123456')
    print(f"\n── Stabilité du hash ──")
    print(f"  hash1 : {hash1[:20]}...")
    print(f"  hash2 : {hash2[:20]}...")
    print(f"  Stable : {'✓ OUI' if hash1 == hash2 else '✗ NON'}")