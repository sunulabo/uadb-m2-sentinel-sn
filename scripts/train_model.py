import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder

# Création du dossier pour les rapports si inexistant
os.makedirs('../rapport', exist_ok=True)

def load_data():
    # Simulation des données lues depuis Hive/Parquet
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

def preprocess_data(df):
    le_region = LabelEncoder()
    le_patho = LabelEncoder()
    
    df['region_encoded'] = le_region.fit_transform(df['region'])
    df['pathologie_encoded'] = le_patho.fit_transform(df['code_pathologie'])
    
    # Enregistrer les encodeurs pour le déploiement/dashboard
    os.makedirs('../data_models/encoders', exist_ok=True)
    joblib.dump(le_region, '../data_models/encoders/le_region.pkl')
    joblib.dump(le_patho, '../data_models/encoders/le_patho.pkl')
    
    X = df[['age', 'region_encoded', 'pathologie_encoded']]
    y = df['temperature']
    return X, y, le_region, le_patho

def train_and_evaluate():
    print("Chargement des données...")
    df = load_data()
    X, y, le_region, le_patho = preprocess_data(df)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Entraînement du modèle RandomForestRegressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    # Évaluation (Analyse des scores)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print(f"--- Scores de Performance ---")
    print(f"RMSE : {rmse:.4f}")
    print(f"R²   : {r2:.4f}")
    
    # Sauvegarde du modèle
    joblib.dump(model, '../data_models/sentinel_model.pkl')
    
    # Génération des graphiques PNG
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, alpha=0.5, color='blue')
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
    plt.title("Prédictions vs Valeurs Réelles (Température)")
    plt.xlabel("Valeurs Réelles")
    plt.ylabel("Prédictions")
    plt.tight_layout()
    plt.savefig('../rapport/predictions_vs_actual.png')
    plt.close()
    
    # Importance des features
    features = ['Age', 'Region', 'Pathologie']
    importances = model.feature_importances_
    plt.figure(figsize=(8, 5))
    sns.barplot(x=features, y=importances, palette='viridis')
    plt.title("Importance des Variables (Feature Importance)")
    plt.savefig('../rapport/feature_importance.png')
    plt.close()
    
    print("Graphiques générés dans le dossier 'rapport/'.")
    print("Modèle sauvegardé dans 'data_models/sentinel_model.pkl'.")

if __name__ == "__main__":
    train_and_evaluate()
