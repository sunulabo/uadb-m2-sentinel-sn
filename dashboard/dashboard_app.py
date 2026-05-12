import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
from PIL import Image

st.set_page_config(page_title="Dashboard Sentinel-SN", layout="wide")

st.title("🛡️ Dashboard Épidémiologique - Sentinel-SN")
st.markdown("Ce tableau de bord permet de visualiser les données épidémiologiques et d'utiliser le modèle de Machine Learning pour des prédictions (ex: Température corporelle attendue).")

# --- Section 1: Affichage des graphiques générés par l'entraînement ML ---
st.header("📈 Performances du Modèle ML")
col1, col2 = st.columns(2)

rapport_dir = '../rapport'

try:
    img_pred = Image.open(os.path.join(rapport_dir, 'predictions_vs_actual.png'))
    col1.image(img_pred, caption="Prédictions vs Valeurs Réelles (RMSE/R²)", use_container_width=True)
except FileNotFoundError:
    col1.warning("Le graphique des prédictions n'est pas encore généré. Exécutez le script d'entraînement.")

try:
    img_feat = Image.open(os.path.join(rapport_dir, 'feature_importance.png'))
    col2.image(img_feat, caption="Importance des variables explicatives", use_container_width=True)
except FileNotFoundError:
    col2.warning("Le graphique d'importance des variables n'est pas encore généré.")

# --- Section 2: Prédiction interactive ---
st.header("🔮 Prédiction Interactive")

model_path = '../data_models/sentinel_model.pkl'
le_region_path = '../data_models/encoders/le_region.pkl'
le_patho_path = '../data_models/encoders/le_patho.pkl'

if os.path.exists(model_path) and os.path.exists(le_region_path) and os.path.exists(le_patho_path):
    model = joblib.load(model_path)
    le_region = joblib.load(le_region_path)
    le_patho = joblib.load(le_patho_path)
    
    with st.form("prediction_form"):
        age = st.number_input("Âge du patient", min_value=0, max_value=120, value=30)
        region = st.selectbox("Région", le_region.classes_)
        pathologie = st.selectbox("Pathologie observée", le_patho.classes_)
        
        submitted = st.form_submit_button("Prédire la température probable")
        
        if submitted:
            # Encodage
            reg_enc = le_region.transform([region])[0]
            patho_enc = le_patho.transform([pathologie])[0]
            
            # Prédiction
            prediction = model.predict([[age, reg_enc, patho_enc]])[0]
            
            st.success(f"🌡️ Température corporelle estimée : **{prediction:.2f} °C**")
            
            if prediction > 38.5:
                st.error("⚠️ Alerte fièvre détectée (potentielle épidémie selon les conditions).")
else:
    st.info("Le modèle ML n'est pas encore entraîné ou les encodeurs sont introuvables. Lancez `train_model.py`.")

st.markdown("---")
st.markdown("Projet UADB-M2 - Sentinel-SN (Equipe 02)")
