"""
schema.py — Schéma de validation Pandera pour les données épidémiologiques (Sentinel-SN, Équipe 02)

Valide :
  - id_patient        : hash HMAC-SHA256 (64 chars), unique
  - date_consultation : timestamp passé ou présent
  - age               : [1, 120]
  - sexe              : "M" ou "F"
  - code_pathologie   : liste blanche (PALU, GRIPPE, DENGUE, CHOLERA)
  - region            : liste blanche (5 régions officielles du projet)
  - temperature       : [35.0, 45.0] °C, non nul
"""

import pandera.pandas as pa
from pandera.typing import Series
import pandas as pd

# Listes de référence — source unique de vérité (synchronisées avec kafka_producer.py)
REGIONS_VALIDES = ["Dakar", "Saint-Louis", "Ziguinchor", "Touba", "Thies"]
PATHOLOGIES_VALIDES = ["PALU", "GRIPPE", "DENGUE", "CHOLERA"]


class EpidemiologicalSchema(pa.DataFrameModel):
    """Schéma de validation des données épidémiologiques Sentinel-SN."""

    # ID patient : hash HMAC-SHA256 = exactement 64 caractères hexadécimaux
    id_patient: Series[str] = pa.Field(unique=True, str_length={"min_value": 64, "max_value": 64})

    # Date de consultation : doit être dans le passé ou présent
    date_consultation: Series[pd.Timestamp] = pa.Field()

    # Données démographiques
    age: Series[int] = pa.Field(ge=1, le=120)
    sexe: Series[str] = pa.Field(isin=["M", "F"])

    # Données cliniques — listes blanches strictes
    code_pathologie: Series[str] = pa.Field(isin=PATHOLOGIES_VALIDES, nullable=False)
    region: Series[str] = pa.Field(isin=REGIONS_VALIDES, nullable=False)

    # Température : obligatoire et dans une plage physiologique réaliste
    temperature: Series[float] = pa.Field(ge=35.0, le=45.0, nullable=False)

    @classmethod
    @pa.check("date_consultation")
    def check_date_not_future(cls, series: Series[pd.Timestamp]) -> Series[bool]:
        """Vérifie que la date de consultation n'est pas dans le futur."""
        return series <= pd.Timestamp.now()

    class Config:
        coerce = True   # Conversion automatique des types (ex: str -> Timestamp)
        strict = True   # Erreur si des colonnes imprévues sont présentes


def validate_data(df: pd.DataFrame):
    """Valide un DataFrame selon le schéma EpidemiologicalSchema.

    Args:
        df (pd.DataFrame): Données brutes à valider.

    Returns:
        pd.DataFrame | None: DataFrame validé, ou None si invalide.
    """
    try:
        validated_df = EpidemiologicalSchema.validate(df)
        print("Validation réussie : Les données sont conformes.")
        return validated_df
    except pa.errors.SchemaError as exc:
        print(f"Erreur de validation : {exc}")
        return None
