import pandas as pd
import requests
import os
from collections import Counter
import joblib
import streamlit as st
from agri_assistant_tools import get_market_price
import weather_api


# --- Model Loading Function ---
@st.cache_resource
def load_crop_models():
    """Loads all pre-trained crop models and encoders."""
    try:
        models1 = joblib.load('crop_models_ds1.joblib')
        encoder1 = joblib.load('crop_encoder1.joblib')
        features1 = joblib.load('crop_features1.joblib')
        
        models2 = joblib.load('crop_models_ds2.joblib')
        encoder2 = joblib.load('crop_encoder2.joblib')
        features2 = joblib.load('crop_features2.joblib')
        
        return models1, encoder1, features1, models2, encoder2, features2
    except FileNotFoundError:
        st.error("ERROR: Model files not found. Please run 'python train_crop_models.py' first.")
        st.stop()

# --- Prediction Function ---
def predict_from_input(user_input, models1, encoder1, features1, models2, encoder2, features2):
    all_predictions = []
    user_input_lower = {k.lower(): v for k, v in user_input.items()}
    
    # Ensure feature order is correct
    input_df1 = pd.DataFrame([user_input_lower])[features1]
    input_df2 = pd.DataFrame([user_input_lower])[features2]
    
    for model in models1.values():
        pred_label = encoder1.inverse_transform(model.predict(input_df1))[0]
        all_predictions.append(pred_label)
    for model in models2.values():
        pred_label = encoder2.inverse_transform(model.predict(input_df2))[0]
        all_predictions.append(pred_label)
    
    vote_count = Counter(all_predictions)
    best_crop = vote_count.most_common(1)[0][0]
    
    return best_crop, vote_count


def get_market_price(crop_name: str, state_name: str, district_name: str = None):
    """
    Fetch market prices for the recommended crop.
    Uses AGMARKNET API from Indian government.
    """
    return weather_api.get_market_price_with_district(crop_name, state_name, district_name)