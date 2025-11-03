import streamlit as st
import os
import json
import cv2
from ultralytics import YOLO
import google.generativeai as genai
from googleapiclient.discovery import build
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from PIL import Image

# --- Page Configuration (MUST be the first Streamlit command) ---
st.set_page_config(
    page_title="Pahari Khet Sahayak",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Load API Keys and Environment ---
load_dotenv()

# ===================================================================
# --- MODEL AND API SETUP (Cached for Performance) ---
# ===================================================================

@st.cache_resource
def load_all_models():
    """
    Loads all YOLO models and configures the Google AI client.
    This function is cached by Streamlit, so models are loaded only once.
    """
    print("Loading all models, this might take a moment...")
    try:
        models = {
            'crop_classifier': YOLO('crop_classifier_yolo.pt'),
            'wheat_disease': YOLO('best.pt'),
            'millet_disease': YOLO('final_model_float32.tflite', task='detect'),
            'general_disease': YOLO('generalist_model_float32.tflite', task='detect')
        }
        
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            st.error("❌ ERROR: GOOGLE_API_KEY not found in .env file.")
            st.stop()
        
        genai.configure(api_key=api_key)
        
        print("✅ All models and API clients loaded successfully!")
        return models
    except Exception as e:
        st.error(f"Error loading models: {e}")
        st.stop()

models = load_all_models()

@st.cache_resource
def load_knowledge_base():
    """Loads and processes the local knowledge base, caching the result."""
    if not os.path.exists('./knowledge_base'):
        return None
    
    print("Creating new knowledge base index...")
    loader = DirectoryLoader('./knowledge_base/', glob="**/*.txt", show_progress=True)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_documents(texts, embeddings)
    print("✅ Knowledge base is ready.")
    return vector_store

vector_store = load_knowledge_base()

# ===================================================================
# --- CORE LOGIC (Refactored from main.py and llm_advisor.py) ---
# ===================================================================

def classify_crop(image_path, confidence_threshold=0.85):
    results = models['crop_classifier'].predict(image_path, verbose=False)
    probs = results[0].probs
    confidence = probs.top1conf.item()
    if confidence < confidence_threshold:
        return "Invalid", confidence
    else:
        return models['crop_classifier'].names[probs.top1], confidence

def run_yolo_detection(model_to_use, image_path):
    results = model_to_use.predict(image_path, verbose=False)
    annotated_image = results[0].plot() # BGR image from OpenCV
    
    best_detections = {}
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        name = model_to_use.names[class_id]
        if name not in best_detections or confidence > best_detections[name]["confidence_score"]:
            coords = box.xyxy[0].tolist()
            best_detections[name] = {
                "disease_name": name, "confidence_score": confidence,
                "bounding_box_coordinates": {"x1": int(coords[0]), "y1": int(coords[1]), "x2": int(coords[2]), "y2": int(coords[3])}
            }
    return list(best_detections.values()), annotated_image

def detect_disease(crop_name, image_path):
    simple_crop_name = crop_name.lower().replace(" dataset", "").strip()
    if "wheat" in simple_crop_name:
        return run_yolo_detection(models['wheat_disease'], image_path)
    elif "millet" in simple_crop_name:
        return run_yolo_detection(models['millet_disease'], image_path)
    else:
        return run_yolo_detection(models['general_disease'], image_path)

def google_search(query: str) -> str:
    """Performs a curated search using the official Google API client."""
    try:
        service = build("customsearch", "v1", developerKey=os.environ['GOOGLE_API_KEY'])
        res = service.cse().list(q=query, cx=os.environ['GOOGLE_CSE_ID'], num=2).execute()
        snippets = [f"Source: {item.get('link', 'N/A')}\nContent: {item.get('snippet', '').replace('...', '')}" for item in res.get('items', [])]
        if not snippets:
            return "No relevant information found in trusted online sources."
        return "\n---\n".join(snippets)
    except Exception as e:
        return f"There was an error during the live search: {e}"

# In Disease_Prediction.py
# REPLACE the old get_llm_advice function with this one

def get_llm_advice(crop_name, disease_name, confidence_score):
    """Generates advice using the Hybrid RAG system."""
    with st.spinner(f"Asking Pahari Khet Sahayak about {disease_name}..."):
        # Hybrid Retrieval
        search_query = f"treatment and prevention for {disease_name} on {crop_name} in Uttarakhand"
        live_context = google_search(search_query)
        
        local_context = "No local knowledge base available."
        if vector_store:
            results = vector_store.similarity_search(search_query, k=1)
            if results:
                local_context = results[0].page_content

        prompt = f"""
You are 'Pahari Khet Sahayak', an expert AI agricultural assistant for farmers in Uttarakhand.
Your purpose is to provide clear, reliable, and actionable advice.

You will be given two sources of information:
1.  **Live Search Results:** The most up-to-date information from trusted agricultural websites.
2.  **Local Knowledge Base:** Curated, expert information that is highly relevant.

Your task is to synthesize information from BOTH sources to give the best possible answer. Prioritize the Live Search Results for timeliness, but use the Local Knowledge Base for verification and to add specific details that might be missing.

--- CONTEXT FROM LIVE SEARCH ---
{live_context}
--- END OF CONTEXT ---

--- CONTEXT FROM LOCAL KNOWLEDGE BASE ---
{local_context}
--- END OF CONTEXT ---

Based on a synthesis of BOTH contexts, answer the user's question. Use the vision model's confidence score to adjust your tone:
- If confidence is high (>80%), be direct.
- If confidence is medium (40-80%), say it's a 'possible match' and advise confirming symptoms.
- If confidence is low (<40%), express uncertainty and focus on monitoring.

Question: A {crop_name} plant might have {disease_name}. The vision model's confidence is {confidence_score*100:.0f}%. Provide a detailed treatment and prevention guide.

Follow these steps:
1. Acknowledge the confidence level.
2. Summarize key symptoms from the combined context for the farmer to verify.
3. Provide a step-by-step treatment guide.
4. Provide a clear, bulleted prevention plan.
**CRITICAL SAFETY INSTRUCTION:** If neither context provides enough information, you MUST state: "I could not find enough specific information to provide a reliable answer. It is best to consult a local agricultural expert."

Structure your final response in Markdown with clear sections.
"""
        try:
            llm = genai.GenerativeModel('gemini-pro')
            response = llm.generate_content(prompt)
            
            # --- NEW, MORE ROBUST CHECK ---
            if not response.parts:
                print("\n--- !! DISEASE PREDICTION DEBUGGER !! ---")
                print("Error: The response was blocked by safety filters.")
                print(f"Full Response Object: {response}")
                print("--- !! END OF DEBUGGER !! ---\n")
                st.error("The response was blocked by safety filters. Please try a different image or query.")
                return None
            
            return response.text
        
        except Exception as e:
            # Print the detailed error to the TERMINAL
            print("\n--- !! DISEASE PREDICTION DEBUGGER !! ---")
            print(f"General Error in get_llm_advice:")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Details: {e}")
            print("ACTION: This is likely the 'v1beta' error. Run 'pip install --upgrade google-generativeai'")
            print("--- !! END OF DEBUGGER !! ---\n")
            
            # Show a user-friendly error in the app
            st.error(f"An error occurred while getting advice from the Gemini API. Please check the terminal logs for details.")
            st.error(f"Error details (for user): {e}") # This will show the v1beta error
            return None

# ===================================================================
# --- STREAMLIT USER INTERFACE ---
# ===================================================================

st.title("🌿 Pahari Khet Sahayak")
st.markdown("An AI-powered agricultural assistant for the farmers of Uttarakhand.")
st.markdown("---")

uploaded_file = st.file_uploader("Upload an image of your crop leaf", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save the uploaded file temporarily
    with open("temp_image.jpg", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    col1, col2 = st.columns(2)
    with col1:
        st.image("temp_image.jpg", caption="Uploaded Image", use_column_width=True)

    with st.spinner("Analyzing image... This may take a moment."):
        # --- Stage 1: Classify the crop ---
        crop_type, confidence = classify_crop("temp_image.jpg")
        
        st.header("Stage 1: Crop Identification")
        if crop_type == "Invalid":
            st.error(f"This does not appear to be a supported crop. (Confidence: {confidence:.2%})")
            st.warning("Please upload a clear image of a crop leaf from the 15 supported types.")
        else:
            st.success(f"Detected Crop: **{crop_type}** (Confidence: {confidence:.2%})")

            # --- Stage 2: Detect Diseases ---
            st.header("Stage 2: Disease Detection")
            disease_results, annotated_image_cv2 = detect_disease(crop_type, "temp_image.jpg")
            
            # Convert BGR image from OpenCV to RGB for Streamlit
            annotated_image_rgb = cv2.cvtColor(annotated_image_cv2, cv2.COLOR_BGR2RGB)
            st.image(annotated_image_rgb, caption="Annotated Image with Detections", use_column_width=True)
            
            # --- Stage 3: Generate LLM Advice ---
            st.header("Stage 3: Expert Advice from Pahari Khet Sahayak")
            if not disease_results:
                st.info(f"The {crop_type} plant appears to be healthy. Continue with good farming practices.")
            else:
                for disease in disease_results:
                    disease_name = disease.get("disease_name", "Unknown Disease")
                    confidence_score = disease.get("confidence_score", 1.0)
                    
                    st.subheader(f"Advice for: {disease_name} (Confidence: {confidence_score:.2%})")
                    advice = get_llm_advice(crop_type, disease_name, confidence_score)
                    if advice:
                        st.markdown(advice)