import streamlit as st
import google.generativeai as genai
import agri_assistant_tools as tools # Import our new tools file
import json
import os
from dotenv import load_dotenv
from typing import Tuple
import chat_storage
import connectivity_check
import offline_search
import voice_handler
import tempfile
import base64
import hashlib
import ui_utils

# --- Initialize UI Settings ---
if "ui_language" not in st.session_state:
    st.session_state.ui_language = "en"
if "ui_theme" not in st.session_state:
    st.session_state.ui_theme = "light"

# --- Page Config ---
st.set_page_config(
    page_title="Agri Assistant", 
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS styling
ui_utils.apply_custom_css()

# --- Header with Language and Theme Toggles ---
col_title, col_lang, col_theme = st.columns([3, 1, 1])
with col_title:
    st.title(ui_utils.get_text("title"))
    st.markdown(ui_utils.get_text("subtitle"))
    st.info(ui_utils.get_text("features"))

with col_lang:
    st.markdown("<br>", unsafe_allow_html=True)  # Spacing
    lang_option = st.selectbox(
        ui_utils.get_text("language"),
        ["English", "हिंदी"],
        index=0 if st.session_state.ui_language == "en" else 1,
        key="lang_select",
        on_change=None
    )
    new_lang = "en" if lang_option == "English" else "hi"
    if st.session_state.ui_language != new_lang:
        st.session_state.ui_language = new_lang
        st.rerun()

with col_theme:
    st.markdown("<br>", unsafe_allow_html=True)  # Spacing
    theme_option = st.selectbox(
        ui_utils.get_text("theme"),
        [ui_utils.get_text("light"), ui_utils.get_text("dark")],
        index=0 if st.session_state.ui_theme == "light" else 1,
        key="theme_select",
        on_change=None
    )
    new_theme = "light" if theme_option == ui_utils.get_text("light") else "dark"
    if st.session_state.ui_theme != new_theme:
        st.session_state.ui_theme = new_theme
        st.rerun()

# --- Initialize Chat Storage ---
chat_storage.init_database()

# --- Internet Connectivity Check ---
is_online = connectivity_check.is_online()
if is_online:
    st.success(ui_utils.get_text("online"))
else:
    st.warning(ui_utils.get_text("offline"))

# --- Load API Keys ---
load_dotenv()
if 'GOOGLE_API_KEY' not in os.environ:
    st.error("GOOGLE_API_KEY not found in .env. Please add it to run the assistant.")
    st.stop()
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

# --- Tool-Using AI Setup ---

# This is the "Router" model. It decides which tool to use.
router_model = genai.GenerativeModel('gemini-pro')
router_prompt = """
You are a query routing-and-extraction expert for an agricultural assistant. 
Given a user query, your job is to identify the correct tool to use and extract the necessary parameters.
Your response MUST be a single line of valid JSON.

The available tools are:
1. {"tool": "weather", "location": "..."} - Use for any weather-related questions.
2. {"tool": "market_price", "crop": "...", "state": "..."} - Use for questions about crop prices.
3. {"tool": "general_search", "query": "..."} - Use for all other agricultural questions (e.g., "how to grow rice", "what is wheat rust?").
4. {"tool": "none", "reply": "..."} - Use if the question is a simple greeting, a thank-you, or conversational.

Examples:
User Query: what's the weather in Dehradun?
JSON: {"tool": "weather", "location": "Dehradun"}

User Query: price of wheat in Punjab
JSON: {"tool": "market_price", "crop": "wheat", "state": "Punjab"}

User Query: how to treat blast disease in rice
JSON: {"tool": "general_search", "query": "how to treat blast disease in rice"}

User Query: Hello
JSON: {"tool": "none", "reply": "Hello! How can I help you with your agricultural questions today?"}

User Query: thanks
JSON: {"tool": "none", "reply": "You're welcome! Do you have any other questions?"}

---
User Query: {query}
JSON: 
"""

# This is the "Answer" model. It formulates a final response.
answer_model = genai.GenerativeModel('gemini-pro')
answer_prompt_template = """
You are 'Pahari Khet Sahayak', a helpful AI agricultural assistant.
The user asked the following question:
"{query}"

I have retrieved the following real-time information to help you answer:
--- CONTEXT ---
{context}
--- END OF CONTEXT ---

Based *only* on the context provided, please give a clear, helpful, and natural-language answer to the user.
If the context says the information could not be found, state that clearly.
"""

# --- Input Validation Algorithm ---
validation_model = genai.GenerativeModel('gemini-pro')
validation_prompt = """
You are an input validation system for an agricultural assistant. 
Your task is to determine if a user's query is related to agriculture, farming, or agricultural topics.

A query IS agriculture-related if it asks about:
- Crops, farming, cultivation, planting, harvesting
- Weather for farming/agriculture
- Market prices of crops/agricultural products
- Pesticides, fertilizers, agricultural chemicals
- Plant diseases, crop health, pest control
- Soil, irrigation, agricultural practices
- Agricultural machinery, tools
- Livestock (if it's a mixed farming question)
- Agricultural economics, farming business
- Agricultural research, techniques
- Gardening related to food crops
- General agricultural advice, tips, or information

A query is NOT agriculture-related if it asks about:
- General technology, programming, software
- Cooking recipes (unless asking about crop ingredients)
- Medical health, human diseases, fitness
- Entertainment, movies, games, sports
- Politics, current events (unless agriculture policy)
- History, geography (unless agricultural history)
- Mathematics, science (unless agricultural science)
- Shopping for non-agricultural products
- Travel, tourism (unless agricultural tourism)
- Personal life, relationships, education (unless agricultural education)

Your response MUST be a single line of valid JSON in this format:
{{"is_agriculture_related": true/false, "reason": "brief explanation"}}

Examples:
Query: "What is the price of wheat in Punjab?"
Response: {{"is_agriculture_related": true, "reason": "Query is about crop market prices"}}

Query: "How to grow tomatoes?"
Response: {{"is_agriculture_related": true, "reason": "Query is about crop cultivation"}}

Query: "What is Python programming?"
Response: {{"is_agriculture_related": false, "reason": "Query is about programming, not agriculture"}}

Query: "Hello, how are you?"
Response: {{"is_agriculture_related": true, "reason": "Greeting - should be allowed as conversational"}}

Query: "Tell me a joke"
Response: {{"is_agriculture_related": false, "reason": "General entertainment, not agriculture-related"}}

Query: "What is the weather in Delhi?"
Response: {{"is_agriculture_related": true, "reason": "Weather is important for agriculture"}}

---
User Query: {query}
Response: 
"""

def validate_agriculture_query(query: str) -> Tuple[bool, str]:
    """
    Validates if a user query is related to agriculture.
    
    Returns:
        Tuple of (is_valid: bool, message: str)
        - If valid: (True, "")
        - If invalid: (False, error_message)
    """
    # Allow greetings and basic conversational queries
    query_lower = query.lower().strip()
    greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", 
                 "thanks", "thank you", "bye", "goodbye", "see you"]
    
    # Check for simple greetings first
    if any(query_lower.startswith(g) or query_lower == g for g in greetings):
        return True, ""
    
    # If offline, skip validation (allow all queries for offline mode)
    if not connectivity_check.is_online():
        return True, ""
    
    try:
        # Use LLM to validate the query
        prompt = validation_prompt.format(query=query)
        response = validation_model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Try to parse JSON response
        try:
            # Remove markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            validation_result = json.loads(result_text)
            is_valid = validation_result.get("is_agriculture_related", False)
            
            if is_valid:
                return True, ""
            else:
                reason = validation_result.get("reason", "Query is not related to agriculture")
                message = (
                    "🌾 I'm Pahari Khet Sahayak, an agricultural assistant. "
                    "I can help you with questions about:\n\n"
                    "• **Crops & Farming:** Crop cultivation, planting, harvesting\n"
                    "• **Weather:** Weather forecasts for farming\n"
                    "• **Market Prices:** Crop prices, agricultural economics\n"
                    "• **Pesticides & Fertilizers:** Agricultural chemicals and treatments\n"
                    "• **Crop Diseases:** Plant health, pest control, disease treatment\n"
                    "• **Soil & Irrigation:** Agricultural practices and techniques\n"
                    "• **General Agriculture:** Farming advice, tips, and information\n\n"
                    "Please ask me a question related to agriculture, farming, or crops!"
                )
                return False, message
                
        except json.JSONDecodeError:
            # If JSON parsing fails, fall back to keyword-based validation
            return keyword_based_validation(query)
            
    except Exception as e:
        print(f"Error in validation: {e}")
        # Fallback to keyword-based validation
        return keyword_based_validation(query)

def keyword_based_validation(query: str) -> Tuple[bool, str]:
    """
    Fallback keyword-based validation if LLM validation fails.
    """
    query_lower = query.lower()
    
    # Agriculture-related keywords
    agri_keywords = [
        # Crops & Farming
        "crop", "crops", "farm", "farming", "farmer", "cultivation", "plant", "planting",
        "harvest", "harvesting", "sow", "sowing", "seed", "seeds", "field", "agriculture",
        
        # Specific crops
        "wheat", "rice", "corn", "maize", "barley", "millet", "paddy", "sugarcane",
        "potato", "tomato", "onion", "garlic", "chili", "pepper", "cotton", "jute",
        
        # Weather
        "weather", "rain", "rainfall", "temperature", "humidity", "climate", "monsoon",
        "drought", "frost", "season", "climate change",
        
        # Market & Prices
        "price", "prices", "market", "mandi", "rate", "cost", "rupee", "quintal",
        "economic", "profit", "loss", "selling",
        
        # Pesticides & Chemicals
        "pesticide", "fertilizer", "fertiliser", "insecticide", "herbicide", "fungicide",
        "chemical", "organic", "inorganic", "urea", "dap", "npk",
        
        # Diseases & Pests
        "disease", "pest", "insect", "fungus", "rust", "blight", "mosaic", "virus",
        "bacterial", "treatment", "cure", "prevention", "control",
        
        # Soil & Irrigation
        "soil", "irrigation", "water", "fertilizer", "nutrient", "nitrogen", "phosphorus",
        "potassium", "ph", "compost", "manure",
        
        # General agriculture
        "agricultural", "farming", "crop rotation", "intercropping", "organic farming",
        "sustainable", "yield", "production", "acre", "hectare"
    ]
    
    # Check if query contains agriculture-related keywords
    has_agri_keyword = any(keyword in query_lower for keyword in agri_keywords)
    
    # Non-agriculture keywords (if present alone, likely not agriculture)
    non_agri_keywords = [
        "python", "programming", "code", "software", "app", "website",
        "movie", "film", "song", "music", "game", "sport", "football", "cricket",
        "cooking recipe", "how to cook", "restaurant", "recipe for",
        "medical", "doctor", "hospital", "medicine", "health check",
        "shopping", "buy", "shop", "product"  # unless with crop keyword
    ]
    
    # Strong non-agriculture indicators
    if any(keyword in query_lower for keyword in non_agri_keywords):
        if not has_agri_keyword:
            return False, (
                "🌾 I'm Pahari Khet Sahayak, an agricultural assistant. "
                "I specialize in agriculture, farming, crops, weather, market prices, and related topics. "
                "Please ask me a question related to agriculture!"
            )
    
    # If it has agriculture keywords or is short (likely greeting), allow it
    if has_agri_keyword or len(query.split()) <= 3:
        return True, ""
    
    # If unclear, allow it (lenient approach)
    return True, ""

# In pages/3_Agri_Assistant.py
# REPLACE the old function with this new one:

def get_ai_response(query, use_offline=False):
    """
    This is the main function that routes, calls tools, and generates an answer.
    If offline or use_offline=True, searches chat history for similar queries.
    """
    # Step 0: Input Validation - Check if query is agriculture-related
    is_valid, validation_message = validate_agriculture_query(query)
    if not is_valid:
        return validation_message, "validation", None
    
    # Check if we should use offline mode
    if use_offline or not connectivity_check.is_online():
        similar_chats = offline_search.find_similar_chats(query, top_k=3)
        if similar_chats:
            # Return formatted offline response
            return offline_search.format_offline_response(similar_chats, query), "offline_search", None
        else:
            return (
                "I'm currently offline and couldn't find any similar questions in your chat history. "
                "Please check your internet connection to get real-time answers.",
                "offline_search",
                None
            )
    
    # Step 1: Route the query to the correct tool
    raw_response_text = "" # <-- New variable for debugging
    try:
        prompt = router_prompt.format(query=query)
        response = router_model.generate_content(prompt)
        raw_response_text = response.text # <-- Store the raw text
        tool_call = json.loads(raw_response_text)

    except json.JSONDecodeError as e:
        # This catches errors if the AI's response is NOT valid JSON
        print("\n--- !! A-G-R-I ASSISTANT DEBUGGER !! ---")
        print(f"JSONDecodeError: The AI's response was not valid JSON.")
        print(f"AI Raw Response: {raw_response_text}")
        print(f"Error Details: {e}")
        print("--- !! END OF DEBUGGER !! ---\n")
        # Try offline search as fallback
        similar_chats = offline_search.find_similar_chats(query, top_k=1)
        if similar_chats:
            return offline_search.format_offline_response(similar_chats, query), "offline_fallback", None
        return "I'm sorry, I received an invalid response from my internal logic. Please try rephrasing.", "error", None

    except Exception as e:
        # This catches all other errors (like API keys)
        print("\n--- !! A-G-R-I ASSISTANT DEBUGGER !! ---")
        print(f"General Error in Step 1 (Tool Routing):")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Details: {e}")
        # If we got a response object, print its text.
        if raw_response_text:
            print(f"AI Raw Response (if available): {raw_response_text}")
        print("ACTION: Check your GOOGLE_API_KEY, and ensure the Generative Language API is enabled in your Google Cloud project with billing.")
        print("--- !! END OF DEBUGGER !! ---\n")
        
        # Give a more specific error to the user
        # Try offline search as fallback
        similar_chats = offline_search.find_similar_chats(query, top_k=1)
        if similar_chats:
            return offline_search.format_offline_response(similar_chats, query), "offline_fallback", None
        
        if "API key" in str(e):
            return "I'm sorry, I'm having an issue with my internal configuration (API Key). The server logs have more details.", "error", None
        return "I'm sorry, I had an internal error trying to understand your request. Please rephrase and try again.", "error", None

    tool_name = tool_call.get("tool")
    
    # Step 2: Call the selected tool (or not)
    context = ""
    context_data = {"tool": tool_name}
    
    if tool_name == "weather":
        if 'location' not in tool_call:
            return "You asked about weather, but didn't specify a location. Please ask again (e.g., 'weather in Delhi').", "error", None
        location = tool_call["location"]
        context = tools.get_weather(location)
        context_data["location"] = location
        
    elif tool_name == "market_price":
        if 'crop' not in tool_call or 'state' not in tool_call:
            return "You asked for a price, but I need both a crop and a state (e.g., 'price of rice in Haryana').", "error", None
        crop = tool_call["crop"]
        state = tool_call["state"]
        context = tools.get_market_price(crop, state)
        context_data["crop"] = crop
        context_data["state"] = state
        
    elif tool_name == "general_search":
        if 'query' not in tool_call:
            return "I'm not sure how to search for that. Could you be more specific?", "error", None
        search_query = tool_call["query"]
        context = tools.google_search(search_query)
        context_data["query"] = search_query
        
    elif tool_name == "none":
        reply = tool_call.get("reply", "Hello! How can I help?")
        return reply, "none", None
        
    else:
        return "I'm sorry, I don't have a tool to answer that question.", "error", None

    # Step 3: Generate the final answer using the tool's context
    try:
        prompt = answer_prompt_template.format(query=query, context=context)
        response = answer_model.generate_content(prompt)
        return response.text, tool_name, context_data
    except Exception as e:
        print(f"Error in Step 3 (Final Answer Generation): {e}")
        # Try offline search as fallback
        similar_chats = offline_search.find_similar_chats(query, top_k=1)
        if similar_chats:
            return offline_search.format_offline_response(similar_chats, query), "offline_fallback", None
        return "I found some information, but had trouble formulating a final answer.", "error", None



# --- Sidebar for Settings and Chat Management ---
with st.sidebar:
    st.header("⚙️ " + ui_utils.get_text("chat_history"))
    
    # New Chat button (prominent)
    if st.button("✨ " + ui_utils.get_text("new_chat"), use_container_width=True, type="primary"):
        st.session_state.messages = []
        if "voice_prompt" in st.session_state:
            del st.session_state.voice_prompt
        if "last_processed_audio_hash" in st.session_state:
            del st.session_state.last_processed_audio_hash
        st.rerun()
    
    st.markdown("---")
    
    chat_count = chat_storage.get_chat_count()
    st.caption(ui_utils.get_text("total_conversations") + f" {chat_count}")
    
    # Option to view chat history
    if st.button("📜 " + ui_utils.get_text("view_history"), use_container_width=True):
        st.session_state.show_history = True
    
    # Option to clear chat history
    if st.button("🗑️ " + ui_utils.get_text("clear_history"), use_container_width=True, type="secondary"):
        chat_storage.clear_chat_history()
        st.session_state.messages = []
        st.success(ui_utils.get_text("clear_history") + " ✅" if st.session_state.ui_language == "hi" else "Chat history cleared! ✅")
        st.rerun()
    
    st.markdown("---")
    
    # Option to force offline mode (for testing)
    force_offline = st.checkbox(ui_utils.get_text("force_offline"), value=False)

# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Don't auto-load history - let user start fresh or view via "View History" button

# Display chat history view if requested
if st.session_state.get("show_history", False):
    with st.expander("📜 Chat History", expanded=True):
        all_chats = chat_storage.get_all_chats(limit=20)
        if all_chats:
            for i, chat in enumerate(all_chats):
                st.markdown(f"**{i+1}. {chat['user_query']}**")
                st.markdown(f"*{chat['timestamp']}*")
                st.markdown(chat['assistant_response'][:200] + "..." if len(chat['assistant_response']) > 200 else chat['assistant_response'])
                st.divider()
        else:
            st.info(ui_utils.get_text("no_chat_history"))
        
        if st.button(ui_utils.get_text("close_history")):
            st.session_state.show_history = False
            st.rerun()

# --- Voice Input Section ---
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("**💬 Text Input**")
with col2:
    st.markdown("**🎤 Voice Input**")

# Voice recording section
audio_file = None
transcribed_text = None
detected_lang = None

# Check if audio_recorder is available
try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False
    st.info("💡 **Voice feature:** Install `audio-recorder-streamlit` for voice input: `pip install audio-recorder-streamlit`")

if AUDIO_RECORDER_AVAILABLE:
    audio_bytes = audio_recorder(
        text="🎤 " + ui_utils.get_text("voice_click"),
        recording_color="#e74c3c",
        neutral_color="#6c757d",
        icon_name="microphone",
        icon_size="2x",
        pause_threshold=2.0
    )
    
    # Only process audio if:
    # 1. We have audio bytes
    # 2. We haven't already processed this specific audio (check hash)
    # 3. We're not currently processing a voice prompt (to avoid loops)
    # 4. We don't have a pending voice_prompt to process
    if audio_bytes:
        # Create a hash of the audio to track if we've processed it
        audio_hash = hashlib.md5(audio_bytes).hexdigest()
        last_processed_hash = st.session_state.get("last_processed_audio_hash", None)
        
        # Only process if this is a new audio recording
        if (audio_hash != last_processed_hash and 
            not st.session_state.get("voice_prompt") and 
            not st.session_state.get("processing_voice")):
            
            # Mark that we're processing to prevent loops
            st.session_state.processing_voice = True
            st.session_state.last_processed_audio_hash = audio_hash
            
            # Process the recorded audio
            with st.spinner("🎤 " + ui_utils.get_text("transcribing")):
                # Transcribe and translate if needed
                original_text, english_text, detected_lang = voice_handler.voice_handler.transcribe_audio_bytes(audio_bytes, language="auto")
                
                if original_text and english_text:
                    # Show original transcription
                    if detected_lang and detected_lang.lower() in ["hi", "hindi"]:
                        st.success(f"✅ **Hindi:** {original_text}")
                        st.info(f"🔄 **English (for processing):** {english_text}")
                    else:
                        st.success(f"✅ **English:** {original_text}")
                    
                    # Store both original and English text
                    st.session_state.voice_prompt = english_text  # Use English for processing
                    st.session_state.voice_original_text = original_text  # Store original for display
                    st.session_state.voice_detected_lang = detected_lang
                    st.session_state.voice_english_text = english_text
                    # Clear the processing flag before rerun
                    st.session_state.processing_voice = False
                    st.rerun()  # Rerun to process the transcribed text
                else:
                    # Clear processing flag and hash on error (so user can try again)
                    st.session_state.processing_voice = False
                    if "last_processed_audio_hash" in st.session_state:
                        del st.session_state.last_processed_audio_hash
                    st.error("❌ Could not transcribe audio. Please ensure:")
                    st.error("   • You have a stable internet connection")
                    st.error("   • You spoke clearly in Hindi or English")
                    st.error("   • The recording is not too short (speak for at least 2-3 seconds)")
                    st.error("   • Try again or use text input instead")

# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Add audio player if it's an assistant message and has audio
        if message["role"] == "assistant" and "audio_base64" in message:
            audio_html = f"""
            <audio controls autoplay style="width: 100%; margin-top: 10px;">
                <source src="data:audio/mpeg;base64,{message['audio_base64']}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)

# Get new user input (text or voice)
prompt = None
is_voice_input = False

# Check for voice input first (process the transcribed text)
if AUDIO_RECORDER_AVAILABLE and st.session_state.get("voice_prompt"):
    prompt = st.session_state.voice_prompt  # This is already in English (translated if needed)
    original_text = st.session_state.get("voice_original_text", prompt)
    detected_lang = st.session_state.get("voice_detected_lang", "en")
    is_voice_input = True
    # Clear all voice-related session state to prevent reprocessing
    # This allows new recordings to be processed
    del st.session_state.voice_prompt
    if "voice_original_text" in st.session_state:
        del st.session_state.voice_original_text
    if "voice_detected_lang" in st.session_state:
        del st.session_state.voice_detected_lang
    if "voice_english_text" in st.session_state:
        del st.session_state.voice_english_text
    if "processing_voice" in st.session_state:
        del st.session_state.processing_voice
    # Note: We keep last_processed_audio_hash to prevent reprocessing the same audio
    # It will be cleared when a new recording with different hash is detected

# Then check for text input
if not prompt:
    prompt = st.chat_input(ui_utils.get_text("ask_here") + " (or use voice input above)")

# Process the prompt (from text or voice)
if prompt:
    # Add user message to chat history
    user_message_content = prompt
    original_text = st.session_state.get("voice_original_text", None) if is_voice_input else None
    
    if is_voice_input and detected_lang and detected_lang != "en":
        user_message_content = f"🎤 [{detected_lang}] {prompt}"
    
    st.session_state.messages.append({"role": "user", "content": user_message_content})
    # Display user message
    with st.chat_message("user"):
        if is_voice_input:
            if original_text and original_text != prompt:
                # Show original Hindi text and English translation
                st.markdown(f"🎤 **Voice (Hindi):** {original_text}")
                st.markdown(f"🔄 **English:** {prompt}")
            else:
                st.markdown(f"🎤 **Voice:** {prompt}")
        else:
            st.markdown(prompt)

    # Get and display AI response
    with st.chat_message("assistant"):
        with st.spinner(ui_utils.get_text("thinking")):
            # Check if we should use offline mode
            use_offline = force_offline or not connectivity_check.is_online()
            
            # Get response (now returns tuple: response, tool_used, context_data)
            result = get_ai_response(prompt, use_offline=use_offline)
            
            # Handle both old format (string) and new format (tuple)
            if isinstance(result, tuple):
                response, tool_used, context_data = result
            else:
                response = result
                tool_used = None
                context_data = None
            
            st.markdown(response)
            
            # Determine output language based on input language
            output_lang = "hi" if (is_voice_input and detected_lang and detected_lang.lower() in ["hi", "hindi"]) else "en"
            
            # Translate response to Hindi if input was in Hindi
            response_in_output_lang = response
            if output_lang == "hi" and detected_lang and detected_lang.lower() in ["hi", "hindi"]:
                try:
                    translated_response, _ = voice_handler.voice_handler.translate_text(response, source_lang="en", target_lang="hi")
                    if translated_response:
                        response_in_output_lang = translated_response
                        # Show both languages
                        with st.expander("🌐 View in both languages", expanded=False):
                            st.markdown(f"**English:**\n{response}")
                            st.markdown(f"\n**हिंदी (Hindi):**\n{translated_response}")
                except Exception as e:
                    print(f"Translation error: {e}")
                    # If translation fails, use English response
            
            # Generate audio output in the appropriate language
            audio_base64 = None
            audio_base64_hindi = None
            try:
                # Generate audio in output language (Hindi if input was Hindi, else English)
                audio_base64 = voice_handler.voice_handler.text_to_speech_base64(response_in_output_lang, language=output_lang)
                
                # Also generate English audio if output is in Hindi (for bilingual support)
                if output_lang == "hi":
                    audio_base64_hindi = audio_base64
                    audio_base64 = voice_handler.voice_handler.text_to_speech_base64(response, language="en")
                
                if audio_base64:
                    # Display audio player
                    lang_label = "हिंदी (Hindi)" if output_lang == "hi" else "English"
                    audio_html = f"""
                    <div style="margin-top: 15px;">
                        <strong>🔊 Audio Response ({lang_label}):</strong>
                        <audio controls autoplay style="width: 100%; margin-top: 5px;">
                            <source src="data:audio/mpeg;base64,{audio_base64}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                    </div>
                    """
                    st.markdown(audio_html, unsafe_allow_html=True)
                    
                    # If Hindi audio is also available, show it
                    if audio_base64_hindi:
                        audio_html_hindi = f"""
                        <div style="margin-top: 10px;">
                            <strong>🔊 Audio Response (हिंदी):</strong>
                            <audio controls style="width: 100%; margin-top: 5px;">
                                <source src="data:audio/mpeg;base64,{audio_base64_hindi}" type="audio/mpeg">
                                Your browser does not support the audio element.
                            </audio>
                        </div>
                        """
                        st.markdown(audio_html_hindi, unsafe_allow_html=True)
            except Exception as e:
                print(f"TTS error: {e}")
            
            # Store in message for history (include both languages if available)
            message_content = response
            if output_lang == "hi" and response_in_output_lang != response:
                message_content = f"{response}\n\n---\n\n**हिंदी:** {response_in_output_lang}"
            
            if audio_base64:
                assistant_message = {
                    "role": "assistant", 
                    "content": message_content, 
                    "audio_base64": audio_base64,
                    "language": output_lang
                }
            else:
                assistant_message = {"role": "assistant", "content": message_content, "language": output_lang}
            
    # Add AI response to chat history
    st.session_state.messages.append(assistant_message)
    
    # Save to persistent storage
    try:
        chat_storage.save_chat(
            user_query=prompt,
            assistant_response=response,
            tool_used=tool_used,
            context_data=context_data
        )
    except Exception as e:
        print(f"Error saving chat to database: {e}")