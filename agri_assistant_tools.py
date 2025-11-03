import os
import requests
import json
from googleapiclient.discovery import build

# --- Tool 1: Google Search (Copied from your Disease Predictor) ---
def google_search(query: str) -> str:
    """Performs a curated search using the official Google API client."""
    print(f"Executing Google Search for: {query}")
    try:
        api_key = os.environ['GOOGLE_API_KEY']
        cse_id = os.environ['GOOGLE_CSE_ID']
        
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, num=3).execute()
        
        snippets = []
        for item in res.get('items', []):
            snippets.append(
                f"Source: {item.get('link', 'N/A')}\nTitle: {item.get('title', 'N/A')}\nContent: {item.get('snippet', '').replace('...', '')}"
            )
        
        if not snippets:
            return "No relevant information found in trusted online sources."
        return "\n---\n".join(snippets)
        
    except Exception as e:
        print(f"Error in google_search: {e}")
        return f"There was an error during the live search: {e}"

# --- Tool 2: Market Price (Upgraded version of your old function) ---
def get_market_price(crop_name: str, state_name: str) -> str:
    """
    Fetches AGMARKNET prices for a specific crop and state from data.gov.in.
    """
    print(f"Executing Market Price search for: {crop_name} in {state_name}")
    try:
        API_KEY = os.environ['DATA_GOV_API_KEY']
        api_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        
        params = {
            "api-key": API_KEY, "format": "json", "limit": "20",
            "filters[state]": state_name.title(),
            "filters[commodity]": crop_name.title()
        }
        
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and 'records' in data and data['records']:
            price_info = f"Recent AGMARKNET Market Prices for {crop_name.title()} in {state_name.title()}:\n"
            processed_records = 0
            for record in data['records']:
                if processed_records >= 5: break
                district = record.get('district', 'N/A')
                market = record.get('market', 'N/A')
                modal_price = record.get('modal_price', 'N/A')
                if modal_price and modal_price != '0':
                    price_info += f"  - District: {district}, Market: {market}, Price: ₹{modal_price}/Quintal\n"
                    processed_records += 1
            
            if processed_records == 0:
                 return f"No recent market price data (with valid prices) found for {crop_name.title()} in {state_name.title()}."
            return price_info
        else:
            return f"No market price data found for {crop_name.title()} in {state_name.title()}."
            
    except requests.exceptions.RequestException:
        return "Could not fetch market prices due to a network issue."
    except Exception as e:
        print(f"Error in get_market_price: {e}")
        return f"An error occurred while fetching market prices: {e}"

# --- Tool 3: Weather Report (New Function) ---
def get_weather(location: str) -> str:
    """
    Fetches the current weather for a location using OpenWeatherMap.
    """
    print(f"Executing Weather search for: {location}")
    try:
        API_KEY = os.environ['OPENWEATHER_API_KEY']
        api_url = "http://api.openweathermap.org/data/2.5/weather"
        
        params = {
            "q": location,
            "appid": API_KEY,
            "units": "metric" # Use Celsius
        }
        
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("cod") != 200:
            return f"Could not find weather data for {location}."

        weather_desc = data['weather'][0]['description']
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        
        report = (
            f"Current weather in {data['name']}, {data['sys']['country']}:\n"
            f"  - Conditions: {weather_desc.title()}\n"
            f"  - Temperature: {temp}°C\n"
            f"  - Humidity: {humidity}%\n"
            f"  - Wind Speed: {wind_speed} m/s"
        )
        return report
        
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return f"Could not find weather data for the location: {location}."
        elif response.status_code == 401:
            return "Invalid OpenWeatherMap API key. Please check your .env file."
        else:
            return f"An HTTP error occurred: {http_err}"
    except Exception as e:
        print(f"Error in get_weather: {e}")
        return f"An error occurred while fetching weather: {e}"