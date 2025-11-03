import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import weather_api

# Import the logic functions we created
import crop_recommender_logic as crl

# --- Page Config ---
st.set_page_config(page_title="Crop Recommendation", page_icon="🌾", layout="wide")
st.title("🌾 Crop Recommendation")
st.markdown("Enter your farm's location and soil data to get a crop recommendation with current market prices.")
st.markdown("---")

# --- Load Environment & Models ---
load_dotenv()
models1, encoder1, features1, models2, encoder2, features2 = crl.load_crop_models()

# --- Location Selection Section ---
st.header("📍 Select Your Farm Location")

col_state, col_district, col_fetch = st.columns([2, 2, 1])

with col_state:
    selected_state = st.selectbox(
        "Select State",
        weather_api.INDIAN_STATES,
        index=weather_api.INDIAN_STATES.index("Uttarakhand") if "Uttarakhand" in weather_api.INDIAN_STATES else 0
    )

with col_district:
    # Get districts for selected state
    districts = weather_api.STATE_DISTRICTS.get(selected_state, ["Not Available"])
    selected_district = st.selectbox(
        "Select District/City",
        districts,
        index=0
    )

with col_fetch:
    st.markdown("<br>", unsafe_allow_html=True)
    col_fetch_btn, col_clear_btn = st.columns(2)
    with col_fetch_btn:
        fetch_weather = st.button("🌤️ Fetch", type="primary", use_container_width=True)
    with col_clear_btn:
        clear_weather = st.button("🔄 Clear", use_container_width=True)

# Initialize weather data in session state
if "weather_data" not in st.session_state:
    st.session_state.weather_data = None

# Clear weather data if requested
if clear_weather:
    st.session_state.weather_data = None
    st.success("✅ Weather data cleared!")
    st.rerun()

# Auto-fetch weather data
if fetch_weather and selected_district != "Not Available":
    with st.spinner(f"🌤️ Fetching weather data for {selected_district}, {selected_state}..."):
        weather_data = weather_api.get_weather_data(
            city_name=selected_district,
            state=selected_state,
            district=selected_district
        )
        
        if weather_data.get("temperature") is not None:
            st.session_state.weather_data = weather_data
            st.success(f"✅ Weather data fetched successfully!")
            st.info(f"🌡️ **Temperature:** {weather_data['temperature']}°C | 💧 **Humidity:** {weather_data['humidity']}% | 🌧️ **Rainfall:** {weather_data['rainfall']} mm/day")
            st.rerun()
        else:
            st.warning("⚠️ Could not fetch weather data. Please enter manually or check your API keys.")
            st.info("💡 **Note:** You need OPENWEATHER_API_KEY in your .env file. Get a free key from: https://openweathermap.org/api")

# Use stored weather data if available
weather_data = st.session_state.weather_data

# Show weather data status if available
if weather_data and weather_data.get("temperature") is not None:
    st.info(f"✅ **Weather Data Loaded:** {selected_district}, {selected_state} - 🌡️ {weather_data['temperature']}°C | 💧 {weather_data['humidity']}% | 🌧️ {weather_data['rainfall']} mm/day")

# --- User Input Form ---
st.header("📊 Enter Your Farm's Conditions")
if weather_data and weather_data.get("temperature") is not None:
    st.markdown("✅ **Weather data will be auto-filled below.** You can modify values manually if needed.")
else:
    st.markdown("💡 **Tip:** Select your location above and click '🌤️ Fetch' to auto-fill weather data, or enter manually below.")

with st.form(key="crop_form"):
    # Create columns for a cleaner layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        n_val = st.number_input("Nitrogen (N) value", min_value=0.0, max_value=200.0, value=90.0, step=1.0, help="Soil nitrogen content")
        # Auto-fill temperature if weather data available
        temp_default = weather_data.get("temperature") if weather_data and weather_data.get("temperature") is not None else 20.8
        temp_val = st.number_input("Temperature (°C)", min_value=-10.0, max_value=60.0, value=float(temp_default), step=0.1, format="%.1f", help="Current temperature")
        ph_val = st.number_input("pH value", min_value=0.0, max_value=14.0, value=6.5, step=0.1, format="%.1f", help="Soil pH level")

    with col2:
        p_val = st.number_input("Phosphorus (P) value", min_value=0.0, max_value=200.0, value=42.0, step=1.0, help="Soil phosphorus content")
        # Auto-fill humidity if weather data available
        hum_default = weather_data.get("humidity") if weather_data and weather_data.get("humidity") is not None else 82.0
        hum_val = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=float(hum_default), step=0.1, format="%.1f", help="Current humidity")
        # Auto-fill rainfall if weather data available
        rain_default = weather_data.get("rainfall") if weather_data and weather_data.get("rainfall") is not None else 202.9
        rain_val = st.number_input("Rainfall (mm)", min_value=0.0, max_value=1000.0, value=float(rain_default), step=0.1, format="%.1f", help="Rainfall per day in mm")

    with col3:
        k_val = st.number_input("Potassium (K) value", min_value=0.0, max_value=200.0, value=43.0, step=1.0, help="Soil potassium content")

    submit_button = st.form_submit_button(label="🌾 Get Crop Recommendation", type="primary", use_container_width=True)

# --- Process the Input ---
if submit_button:
    new_data = {
        'n': n_val, 'p': p_val, 'k': k_val,
        'temperature': temp_val, 'humidity': hum_val,
        'ph': ph_val, 'rainfall': rain_val
    }
    
    with st.spinner("🔍 Analyzing conditions and finding the best crop..."):
        recommended_crop, votes = crl.predict_from_input(
            new_data, 
            models1, encoder1, features1, 
            models2, encoder2, features2
        )
    
    # Display Results
    st.header("📊 Prediction Results")
    st.markdown("---")
    
    # Analysis section
    st.subheader("🤖 AI Analysis")
    st.write(f"Based on your farm's conditions, the AI models voted as follows:")
    
    # Display votes in a nicer format
    vote_df = pd.DataFrame(list(votes.items()), columns=['Crop', 'Votes'])
    vote_df = vote_df.sort_values('Votes', ascending=False)
    st.dataframe(vote_df, use_container_width=True, hide_index=True)
    
    # Winner
    st.success(f"🏆 **Recommended Crop: {recommended_crop.title()}**")
    
    st.markdown("---")
    
    # Market Price Section
    st.subheader("💰 Market Price Information")
    st.markdown(f"Fetching current market prices for **{recommended_crop.title()}** in **{selected_district}, {selected_state}**...")
    
    with st.spinner("📡 Fetching market prices from AGMARKNET..."):
        price_details = crl.get_market_price(
            crop_name=recommended_crop,
            state_name=selected_state,
            district_name=selected_district if selected_district != "Not Available" else None
        )
    
    # Display price information
    st.markdown(price_details)
    
    # Additional information
    st.markdown("---")
    st.subheader("📝 Additional Information")
    st.info(f"""
    **Location:** {selected_district}, {selected_state}
    
    **Soil Conditions:**
    - Nitrogen (N): {n_val}
    - Phosphorus (P): {p_val}
    - Potassium (K): {k_val}
    - pH: {ph_val}
    
    **Weather Conditions:**
    - Temperature: {temp_val}°C
    - Humidity: {hum_val}%
    - Rainfall: {rain_val} mm/day
    """)