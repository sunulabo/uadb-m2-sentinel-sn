# test_privacy.py — Tests de vérification PII
# Équipe 02 | FALL Ahmed | UADB 2025-2026

import pytest
from privacy_layer import (
    hacher_identifiant,
    anonymiser_message,
    verifier_absence_pii,
    anonymiser_dataframe,
    PII_FIELDS
)
import pandas as pd


# ── Fixtures ───────────────────────────────────────────────

@pytest.fixture
def message_brut():
    return {
        'patient_raw_id':   'SN001123456',
        'district_id':      1,
        'district_nom':     'Dakar',
        'maladie_code':     'PALUD',
        'nombre_cas':       15,
        'nombre_deces':     1,
        'date_declaration': '2025-08-15',
        'source_rapport':   'HOPITAL'
    }


# ── Tests hachage ──────────────────────────────────────────

def test_hash_non_vide():
    """Le hash ne doit pas être vide."""
    h = hacher_identifiant('SN001123456')
    assert len(h) == 64   # SHA-256 = 64 caractères hex

def test_hash_stable():
    """Même entrée doit toujours donner même hash."""
    h1 = hacher_identifiant('SN001123456')
    h2 = hacher_identifiant('SN001123456')
    assert h1 == h2

def test_hash_different_ids():
    """Deux IDs différents donnent des hashs différents."""
    h1 = hacher_identifiant('SN001123456')
    h2 = hacher_identifiant('SN002654321')
    assert h1 != h2

def test_hash_irreversible():
    """Le hash ne doit pas contenir l'ID original."""
    raw_id = 'SN001123456'
    h = hacher_identifiant(raw_id)
    assert raw_id not in h


# ── Tests anonymisation ────────────────────────────────────

def test_patient_raw_id_supprime(message_brut):
    """patient_raw_id doit être absent après anonymisation."""
    result = anonymiser_message(message_brut)
    assert 'patient_raw_id' not in result

def test_patient_id_secure_present(message_brut):
    """patient_id_secure doit être présent après anonymisation."""
    result = anonymiser_message(message_brut)
    assert 'patient_id_secure' in result

def test_donnees_medicales_conservees(message_brut):
    """Les données médicales non-PII doivent rester intactes."""
    result = anonymiser_message(message_brut)
    assert result['district_id']      == 1
    assert result['maladie_code']      == 'PALUD'
    assert result['nombre_cas']        == 15
    assert result['nombre_deces']      == 1
    assert result['date_declaration']  == '2025-08-15'

def test_aucun_pii_dans_message_anonymise(message_brut):
    """Aucun champ PII ne doit subsister."""
    result = anonymiser_message(message_brut)
    assert verifier_absence_pii(result) is True

def test_verifier_pii_detecte_fuite():
    """verifier_absence_pii doit détecter un message non anonymisé."""
    message_non_anonymise = {'patient_raw_id': 'SN001123456', 'maladie_code': 'PALUD'}
    assert verifier_absence_pii(message_non_anonymise) is False


# ── Tests DataFrame ────────────────────────────────────────

def test_dataframe_anonymise():
    """Le DataFrame anonymisé ne doit contenir aucune colonne PII."""
    df = pd.DataFrame([{
        'patient_raw_id': 'SN001111',
        'district_id': 1,
        'maladie_code': 'CHOLERA',
        'nombre_cas': 5
    }])
    df_secure = anonymiser_dataframe(df)
    for champ in PII_FIELDS:
        assert champ not in df_secure.columns
    assert 'patient_id_secure' in df_secure.columns


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
