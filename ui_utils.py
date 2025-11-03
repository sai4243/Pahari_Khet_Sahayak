"""
UI Utilities Module
Provides language translations and theme management for the application.
"""
import streamlit as st

# Language translations
TRANSLATIONS = {
    "en": {
        "title": "🤖 Agri-Assistant",
        "subtitle": "Ask me about weather, market prices, or any other **agricultural** question.",
        "features": "💡 **Features:** Agriculture-focused | 💾 Chat History | 📴 Offline Mode | 🎤 Voice Input (any language) | 🔊 Voice Output",
        "online": "🟢 Online - Real-time assistance available",
        "offline": "⚠️ Offline - Using chat history for answers",
        "new_chat": "New Chat",
        "clear_history": "Clear Chat History",
        "view_history": "View Chat History",
        "language": "Language",
        "theme": "Theme",
        "light": "Light",
        "dark": "Dark",
        "thinking": "Thinking...",
        "ask_here": "Ask your question here...",
        "voice_click": "Click to record your question",
        "transcribing": "Transcribing your voice (Hindi/English)...",
        "no_chat_history": "No chat history available.",
        "close_history": "Close History",
        "chat_history": "Chat History",
        "total_conversations": "Total conversations:",
        "force_offline": "Force Offline Mode (Testing)",
    },
    "hi": {
        "title": "🤖 कृषि-सहायक",
        "subtitle": "मुझसे मौसम, बाजार कीमतों, या किसी अन्य **कृषि** संबंधी प्रश्न पूछें।",
        "features": "💡 **विशेषताएं:** कृषि-केंद्रित | 💾 चैट इतिहास | 📴 ऑफलाइन मोड | 🎤 आवाज़ इनपुट (किसी भी भाषा) | 🔊 आवाज़ आउटपुट",
        "online": "🟢 ऑनलाइन - वास्तविक समय सहायता उपलब्ध",
        "offline": "⚠️ ऑफलाइन - उत्तरों के लिए चैट इतिहास का उपयोग कर रहे हैं",
        "new_chat": "नई चैट",
        "clear_history": "चैट इतिहास साफ़ करें",
        "view_history": "चैट इतिहास देखें",
        "language": "भाषा",
        "theme": "थीम",
        "light": "हल्का",
        "dark": "गहरा",
        "thinking": "सोच रहा है...",
        "ask_here": "अपना प्रश्न यहाँ पूछें...",
        "voice_click": "अपना प्रश्न रिकॉर्ड करने के लिए क्लिक करें",
        "transcribing": "आपकी आवाज़ ट्रांसक्राइब कर रहे हैं (हिंदी/अंग्रेजी)...",
        "no_chat_history": "कोई चैट इतिहास उपलब्ध नहीं है।",
        "close_history": "इतिहास बंद करें",
        "chat_history": "चैट इतिहास",
        "total_conversations": "कुल बातचीत:",
        "force_offline": "ऑफलाइन मोड फ़ोर्स करें (परीक्षण)",
    }
}


def get_text(key: str) -> str:
    """Get translated text for current language."""
    lang = st.session_state.get("ui_language", "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


def apply_custom_css():
    """Apply custom CSS styling for beautiful UI with dynamic theme support."""
    is_dark = st.session_state.get("ui_theme", "light") == "dark"
    
    if is_dark:
        css = """
        /* Dark Theme Styles */
        .stApp {
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        }
        .stChatMessage {
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 15px;
            margin: 10px 0;
        }
        .stButton>button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .stSuccess {
            background-color: rgba(46, 213, 115, 0.2);
            border-left: 4px solid #2ed573;
        }
        .stInfo {
            background-color: rgba(52, 152, 219, 0.2);
            border-left: 4px solid #3498db;
        }
        h1, h2, h3 {
            color: #ffffff !important;
        }
        """
    else:
        css = """
        /* Light Theme Styles */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .stChatMessage {
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 12px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .stButton>button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .stSuccess {
            background-color: rgba(46, 213, 115, 0.15);
            border-left: 4px solid #2ed573;
        }
        .stInfo {
            background-color: rgba(52, 152, 219, 0.15);
            border-left: 4px solid #3498db;
        }
        /* Header styling */
        h1 {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            margin-bottom: 10px;
        }
        /* Chat input styling */
        .stChatInputContainer {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 10px;
        }
        /* Sidebar styling */
        .css-1d391kg {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
        }
        """
    
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

