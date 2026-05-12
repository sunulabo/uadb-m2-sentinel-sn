"""
schema.py — Schéma de validation Pandera pour les données épidémiologiques (Sentinel-SN, Équipe 02)

Valide :
  - id_patient  : chaîne hachée (SHA-256), unique
  - date_consultation : timestamp passé ou présent
  - age, sexe, code_pathologie, region, temperature
"""

import pandera.pandas as pa
from pandera.typing import Series
import pandas as pd


# Définition du schéma pour les données épidémiologiques de Sentinel-SN
class EpidemiologicalSchema(pa.DataFrameModel):
    id_patient: Series[str] = pa.Field(unique=True)
    date_consultation: Series[pd.Timestamp] = pa.Field()
    age: Series[int] = pa.Field(ge=0, le=120)
    sexe: Series[str] = pa.Field(isin=["M", "F"])
    code_pathologie: Series[str] = pa.Field(nullable=False)  # Ex: PALU, GRIPPE, DENGUE, CHOLERA
    region: Series[str] = pa.Field(nullable=False)
    temperature: Series[float] = pa.Field(ge=35.0, le=45.0, nullable=True)

    @classmethod
    @pa.check("date_consultation")
    def check_date(cls, series: Series[pd.Timestamp]) -> Series[bool]:
        """Vérifie que la date de consultation n'est pas dans le futur."""
        return series <= pd.Timestamp.now()

    class Config:
        coerce = True   # Conversion automatique des types (ex: str -> Timestamp)
        strict = True   # Erreur si des colonnes imprévues sont présentes


def validate_data(df: pd.DataFrame):
    """Valide les données selon le schéma défini."""
    try:
        validated_df = EpidemiologicalSchema.validate(df)
        print("Validation réussie : Les données sont conformes.")
        return validated_df
    except pa.errors.SchemaError as exc:
        print(f"Erreur de validation : {exc}")
        return None
