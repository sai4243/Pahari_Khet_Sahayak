import os
import json
import google.generativeai as genai
from googleapiclient.discovery import build # Official Google API client
from dotenv import load_dotenv

# --- Automatically load the API keys from the .env file ---
load_dotenv()

# ===================================================================
# --- FINAL SETUP: HYBRID RAG SYSTEM ---
# ===================================================================

# Check if the API keys were loaded correctly
if not all(k in os.environ for k in ['GOOGLE_API_KEY', 'GOOGLE_CSE_ID']):
    print("❌ ERROR: API keys not found in .env file. Please check GOOGLE_API_KEY and GOOGLE_CSE_ID.")
    exit()

# Configure the Google AI client
try:
    genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
    print("✅ Google Generative AI client configured successfully.")
except Exception as e:
    print(f"❌ FATAL ERROR: The provided API key is invalid or has an issue. {e}")
    exit()

# --- Retrieval Functions for the Hybrid System ---

def retrieve_local_knowledge(disease_name: str) -> str:
    """
    Attempts to retrieve context from the local knowledge base .txt file.
    """
    # Create a filename that matches your knowledge base files
    filename = disease_name.replace(" ", "_") + ".txt"
    filepath = os.path.join('knowledge_base', filename)
    
    if os.path.exists(filepath):
        print("Found expert information in local knowledge base.")
        with open(filepath, 'r') as f:
            return f.read()
    return "No information found in the local knowledge base for this specific disease."

def google_search(query: str) -> str:
    """
    Performs a curated search and returns a formatted context string with sources.
    """
    print(f"Searching trusted online sources for: \"{query}\"...")
    try:
        service = build("customsearch", "v1", developerKey=os.environ['GOOGLE_API_KEY'])
        res = service.cse().list(q=query, cx=os.environ['GOOGLE_CSE_ID'], num=3).execute()
        
        # --- MODIFIED: Extract title, link, and snippet for each result ---
        contexts = []
        for item in res.get('items', []):
            title = item.get('title', 'No Title')
            link = item.get('link', 'No Link')
            snippet = item.get('snippet', 'No snippet available.').replace('\n', ' ').replace('...', '')
            
            # Format each source clearly for the LLM
            contexts.append(f"Source Title: {title}\nSource Link: {link}\nContent: {snippet}")
        
        if not contexts:
            return "No relevant information found in trusted sources."
        
        # Join all sources into a single context block
        return "\n\n---\n\n".join(contexts)
        
    except Exception as e:
        print(f"Error during Google Search: {e}")
        return "There was an error searching for information. Please check your Google Cloud project permissions."

# Set up the LLM
llm = genai.GenerativeModel('gemini-2.0-flash')

def get_llm_advice(crop_name: str, disease_name: str, confidence_score: float) -> str:
    """
    Generates advice using the Hybrid RAG system and includes source citations.
    """
    # --- HYBRID RETRIEVAL ---
    search_query = f"treatment and prevention for {disease_name} on {crop_name} in Uttarakhand"
    live_context = google_search(search_query)
    local_context = retrieve_local_knowledge(disease_name)
    # -------------------------
    
    # Construct the advanced, confidence-aware prompt with citation instruction
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
5. --- NEW INSTRUCTION --- At the end of your response, you MUST add a section titled "Sources:" and list the "Source Title" and "Source Link" for each piece of context from the live search that you used.

**CRITICAL SAFETY INSTRUCTION:** If neither context provides enough information, you MUST state: "I could not find enough specific information to provide a reliable answer. It is best to consult a local agricultural expert."

Structure your final response in Markdown with clear sections.
"""
    try:
        response = llm.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred while getting advice from the Gemini API: {e}"

# --- Main Workflow (Unchanged) ---
def main():
    json_path = 'detection_results.json'
    if not os.path.exists(json_path):
        print(f"Error: Results file '{json_path}' not found. Please run 'main.py' first.")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)
        
    crop_name = data.get("crop_name", "Unknown Crop")
    if crop_name == "Invalid":
        print("The vision model determined the image was not a valid crop. No advice will be generated.")
        return

    disease_detections = data.get("disease_detections", [])
    print(f"--- Generating advice for: {crop_name} ---")

    if isinstance(disease_detections, str) and "No diseases detected" in disease_detections:
        advice = f"The {crop_name} plant appears to be healthy. Continue with good farming practices."
        print(advice)
    elif isinstance(disease_detections, list) and disease_detections:
        for disease in disease_detections:
            disease_name = disease.get("disease_name", "Unknown Disease")
            confidence = disease.get("confidence_score", 1.0)
            advice = get_llm_advice(crop_name, disease_name, confidence)
            print("\n" + "="*50)
            print(f"ADVICE FOR: {disease_name.upper()} (CONFIDENCE: {confidence:.2%})")
            print("="*50)
            print(advice)
    else:
        advice = f"The {crop_name} plant appears healthy."
        print(advice)

if __name__ == "__main__":
    main()