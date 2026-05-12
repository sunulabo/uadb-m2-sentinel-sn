"""
train_model.py — Script d'entraînement ML (Sentinel-SN, Équipe 02)

Pipeline :
  1. Chargement des données épidémiologiques (simulation Hive/Parquet)
  2. Pré-traitement et encodage des variables catégorielles
  3. Entraînement d'un modèle RandomForestRegressor
  4. Évaluation : RMSE, R²
  5. Génération des graphiques PNG dans le dossier rapport/
  6. Sauvegarde du modèle et des encodeurs pour le dashboard
"""

import os
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Répertoires de sortie
RAPPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'rapport')
ENCODERS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data_models', 'encoders')
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data_models', 'sentinel_model.pkl')

os.makedirs(RAPPORT_DIR, exist_ok=True)
os.makedirs(ENCODERS_DIR, exist_ok=True)


def load_data() -> pd.DataFrame:
    """Simule la lecture des données épidémiologiques depuis Hive/Parquet.
    
    En production, ce bloc sera remplacé par une lecture Spark/PyArrow
    sur HDFS : spark.read.parquet('/user/equipe02/sentinel_data/analytics/')
    
    Returns:
        pd.DataFrame: Données épidémiologiques simulées.
    """
    np.random.seed(42)
    n_samples = 1000
    regions = ["Dakar", "Saint-Louis", "Ziguinchor", "Touba", "Thies"]
    pathologies = ["PALU", "GRIPPE", "DENGUE", "CHOLERA"]

    data = {
        "age": np.random.randint(1, 85, n_samples),
        "region": np.random.choice(regions, n_samples),
        "code_pathologie": np.random.choice(pathologies, n_samples),
        "temperature": np.random.normal(38.5, 1.5, n_samples)
    }
    return pd.DataFrame(data)


def preprocess_data(df: pd.DataFrame):
    """Encode les colonnes catégorielles et sauvegarde les encodeurs.

    Args:
        df (pd.DataFrame): Données brutes.

    Returns:
        tuple: (X features, y target, encodeur region, encodeur pathologie)
    """
    le_region = LabelEncoder()
    le_patho = LabelEncoder()

    df['region_encoded'] = le_region.fit_transform(df['region'])
    df['pathologie_encoded'] = le_patho.fit_transform(df['code_pathologie'])

    joblib.dump(le_region, os.path.join(ENCODERS_DIR, 'le_region.pkl'))
    joblib.dump(le_patho, os.path.join(ENCODERS_DIR, 'le_patho.pkl'))

    X = df[['age', 'region_encoded', 'pathologie_encoded']]
    y = df['temperature']
    return X, y, le_region, le_patho


def generate_plots(y_test, y_pred, feature_importances: np.ndarray):
    """Génère et sauvegarde les graphiques de performance en PNG.

    Args:
        y_test: Valeurs réelles.
        y_pred: Valeurs prédites.
        feature_importances (np.ndarray): Importances des features du modèle.
    """
    # Graphique 1 : Prédictions vs Valeurs Réelles
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, alpha=0.5, color='royalblue', edgecolors='none')
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2, label='Idéal')
    plt.title("Prédictions vs Valeurs Réelles (Température)")
    plt.xlabel("Valeurs Réelles (°C)")
    plt.ylabel("Prédictions (°C)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RAPPORT_DIR, 'predictions_vs_actual.png'), dpi=150)
    plt.close()

    # Graphique 2 : Importance des Variables
    features = ['Age', 'Region', 'Pathologie']
    plt.figure(figsize=(8, 5))
    ax = sns.barplot(x=features, y=feature_importances, hue=features, palette='viridis', legend=False)
    ax.set_title("Importance des Variables (Feature Importance)")
    ax.set_ylabel("Score d'importance")
    plt.tight_layout()
    plt.savefig(os.path.join(RAPPORT_DIR, 'feature_importance.png'), dpi=150)
    plt.close()


def train_and_evaluate():
    """Orchestre l'entraînement, l'évaluation, et l'export des artefacts ML."""
    print("=" * 45)
    print("  Sentinel-SN — Entraînement du Modèle ML")
    print("=" * 45)

    print("[1/4] Chargement des données...")
    df = load_data()
    X, y, le_region, le_patho = preprocess_data(df)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("[2/4] Entraînement du modèle RandomForestRegressor (n_estimators=100)...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("[3/4] Évaluation des performances...")
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print()
    print("--- Scores de Performance ---")
    print(f"  RMSE : {rmse:.4f} °C")
    print(f"  R²   : {r2:.4f}")
    print()

    print("[4/4] Génération des graphiques et sauvegarde...")
    generate_plots(y_test, y_pred, model.feature_importances_)
    joblib.dump(model, MODEL_PATH)

    print(f"✅ Graphiques sauvegardés dans : {os.path.abspath(RAPPORT_DIR)}")
    print(f"✅ Modèle sauvegardé dans     : {os.path.abspath(MODEL_PATH)}")
    print("=" * 45)


if __name__ == "__main__":
    train_and_evaluate()
