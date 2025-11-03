import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Pahari Khet Sahayak",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded" # Keep sidebar open
)

st.title("🌿 Welcome to Pahari Khet Sahayak!")
st.markdown("An AI-powered agricultural assistant for the farmers of Uttarakhand.")
st.markdown("---")

st.header("How to use this tool:")
st.markdown("""
This application is your all-in-one assistant for farming. Please select a tool from the sidebar on the left:

1.  **🤖 Agri Assistant** *(Recommended - Start Here!)*
    * Ask questions about weather, market prices, or general farming advice.
    * 💾 **Chat History:** All conversations are saved automatically.
    * 📴 **Offline Mode:** If internet is unavailable, answers from your chat history are provided.
    * 🔍 **Smart Search:** Finds similar past questions using AI-powered similarity matching.
    * 🎤 **Voice Input:** Record your questions in Hindi or English - automatically transcribed!
    * 🔊 **Voice Output:** Listen to responses in audio format alongside text.
    * 🌐 **Multi-language:** Supports Hindi and English interface.
    * 🎨 **Beautiful UI:** Modern design with light/dark mode support.

2.  **🌿 Disease Prediction:**
    * Upload an image of a crop leaf (like wheat or millet).
    * The AI will identify the crop, detect any diseases, and provide expert advice on how to treat and prevent it.

3.  **🌾 Crop Recommendation:**
    * Enter your soil and weather conditions (Nitrogen, Phosphorus, Potassium, pH, temperature, etc.).
    * The AI will analyze your data and recommend the best crop to plant, along with recent market prices for that crop in Uttarakhand.

---
""")
st.info("💡 **Tip:** Start with Agri Assistant for the best experience! Select a page from the sidebar to begin.")