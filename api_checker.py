import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from langchain_google_genai import GoogleGenerativeAI

# --- Load API keys from your .env file ---
load_dotenv()
print("Attempting to load API keys from .env file...")

# --- Check for necessary keys ---
if not all(k in os.environ for k in ['GOOGLE_API_KEY', 'GOOGLE_CSE_ID']):
    print("\n❌ FATAL ERROR: API keys not found in .env file. Please check GOOGLE_API_KEY and GOOGLE_CSE_ID.")
    exit()
print("✅ API keys found in .env file.")

# --- Test 1: Custom Search API ---
print("\n--- [CHECK 1] Testing Google Custom Search API... ---")
try:
    service = build("customsearch", "v1", developerKey=os.environ['GOOGLE_API_KEY'])
    # Perform a simple test search
    res = service.cse().list(q="what is wheat rust?", cx=os.environ['GOOGLE_CSE_ID'], num=1).execute()
    print("✅ SUCCESS: Custom Search API is working correctly.")
except Exception as e:
    print(f"❌ FAILED: There was an error with the Custom Search API.")
    print(f"   Error Details: {e}")
    print("   ACTION: Please double-check your API key, CSE ID, and ensure billing is linked to your project.")

# --- Test 2: Generative Language API (Gemini) ---
print("\n--- [CHECK 2] Testing Generative Language API (Gemini)... ---")
try:
    # Perform a simple test generation
    llm = GoogleGenerativeAI(model="gemini-1.5-flash")
    llm.invoke("Hello, world!")
    print("✅ SUCCESS: Generative Language API (Gemini) is working correctly.")
except Exception as e:
    print(f"❌ FAILED: There was an error with the Generative Language API.")
    print(f"   Error Details: {e}")
    print("   ACTION: Please double-check your API key and ensure billing is linked to your project.")

print("\n--- Test Complete ---")