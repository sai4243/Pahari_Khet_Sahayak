"""
Weather API Module
Fetches weather data (temperature, humidity, rainfall) using free APIs.
Supports Indian locations with state, district, and mandal information.
"""
import requests
import os
from typing import Optional, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

# Indian states and major cities/districts mapping
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", 
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi"
]

# Major cities/districts in each state (for weather API lookup)
STATE_DISTRICTS = {
    "Uttarakhand": ["Dehradun", "Haridwar", "Nainital", "Almora", "Udham Singh Nagar", "Pauri", "Chamoli"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Agra", "Varanasi", "Meerut", "Allahabad", "Ghaziabad"],
    "Punjab": ["Chandigarh", "Ludhiana", "Amritsar", "Jalandhar", "Patiala"],
    "Haryana": ["Gurgaon", "Faridabad", "Rohtak", "Panipat", "Karnal"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"],
    "Karnataka": ["Bangalore", "Mysore", "Hubli", "Mangalore", "Belgaum"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Asansol", "Siliguri"],
    "Andhra Pradesh": ["Hyderabad", "Visakhapatnam", "Vijayawada", "Guntur", "Nellore"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam"],
    "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Purnia"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Berhampur", "Sambalpur"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam"],
    "Assam": ["Guwahati", "Silchar", "Dibrugarh", "Jorhat", "Tinsukia"],
    "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Hazaribagh"],
    "Chhattisgarh": ["Raipur", "Bhilai", "Bilaspur", "Korba", "Durg"],
    "Himachal Pradesh": ["Shimla", "Kullu", "Manali", "Dharamshala", "Solan"],
    "Delhi": ["New Delhi", "Central Delhi", "North Delhi", "South Delhi"]
}


def get_weather_openweathermap(city_name: str, state: Optional[str] = None) -> Optional[Dict[str, float]]:
    """
    Fetch weather data using OpenWeatherMap free API.
    Returns temperature (°C), humidity (%), and estimated rainfall if available.
    """
    try:
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        if not api_key:
            return None
        
        # Construct location query
        if state:
            location = f"{city_name}, {state}, India"
        else:
            location = f"{city_name}, India"
        
        api_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": api_key,
            "units": "metric"
        }
        
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("cod") == 200:
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            
            # Get rainfall from rain or precipitation if available
            rainfall = 0.0
            if 'rain' in data and '1h' in data['rain']:
                rainfall = data['rain']['1h'] * 24  # Convert hourly to daily estimate
            elif 'rain' in data and '3h' in data['rain']:
                rainfall = data['rain']['3h'] * 8  # Convert 3h to daily estimate
            
            return {
                "temperature": round(temp, 1),
                "humidity": round(humidity, 1),
                "rainfall": round(rainfall, 1)  # mm per day (estimated)
            }
    except Exception as e:
        print(f"OpenWeatherMap API error: {e}")
    
    return None


def get_weather_weatherstack(city_name: str, state: Optional[str] = None) -> Optional[Dict[str, float]]:
    """
    Fetch weather data using Weatherstack API (free tier available).
    """
    try:
        api_key = os.environ.get('WEATHERSTACK_API_KEY')
        if not api_key:
            return None
        
        location = f"{city_name}, {state}, India" if state else f"{city_name}, India"
        
        api_url = "http://api.weatherstack.com/current"
        params = {
            "access_key": api_key,
            "query": location,
            "units": "m"
        }
        
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'current' in data:
            current = data['current']
            temp = current.get('temperature', 0)
            humidity = current.get('humidity', 0)
            precip = current.get('precip', 0)  # precipitation in mm
            
            return {
                "temperature": round(temp, 1),
                "humidity": round(humidity, 1),
                "rainfall": round(precip * 24, 1) if precip else 0.0  # Convert hourly to daily
            }
    except Exception as e:
        print(f"Weatherstack API error: {e}")
    
    return None


def get_weather_data(city_name: str, state: Optional[str] = None, district: Optional[str] = None) -> Dict[str, float]:
    """
    Fetch weather data using available free APIs.
    Tries multiple APIs and returns the first successful result.
    
    Returns:
        Dict with temperature (°C), humidity (%), and rainfall (mm/day)
        Defaults to None values if all APIs fail
    """
    # Use district if provided, otherwise use city
    location = district if district else city_name
    
    # Try OpenWeatherMap first (most commonly available, free tier)
    weather_data = get_weather_openweathermap(location, state)
    if weather_data and weather_data.get("temperature") is not None:
        return weather_data
    
    # If state/district is in India, try adding "India" to location string
    if state and "India" not in location:
        location_with_country = f"{location}, {state}, India"
        weather_data = get_weather_openweathermap(location_with_country, None)
        if weather_data and weather_data.get("temperature") is not None:
            return weather_data
    
    # Try Weatherstack as fallback (if API key available)
    weather_data = get_weather_weatherstack(location, state)
    if weather_data and weather_data.get("temperature") is not None:
        return weather_data
    
    # Return None values if all APIs fail - user can enter manually
    return {
        "temperature": None,
        "humidity": None,
        "rainfall": None
    }


def get_market_price_with_district(crop_name: str, state_name: str, district_name: Optional[str] = None) -> str:
    """
    Fetch market prices for crop in state/district using AGMARKNET API.
    Enhanced version that supports district filtering.
    """
    try:
        api_key = os.environ.get('DATA_GOV_API_KEY')
        if not api_key:
            return "⚠️ DATA_GOV_API_KEY not found. Please add it to your .env file for market price data."
        
        api_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        
        params = {
            "api-key": api_key,
            "format": "json",
            "limit": "20",
            "filters[state]": state_name.title(),
            "filters[commodity]": crop_name.title()
        }
        
        # Add district filter if provided
        if district_name:
            params["filters[district]"] = district_name.title()
        
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and 'records' in data and data['records']:
            # Filter by district if provided
            records = data['records']
            if district_name:
                records = [r for r in records if r.get('district', '').title() == district_name.title()]
            
            if not records:
                return f"⚠️ No market price data found for {crop_name.title()} in {district_name}, {state_name.title()}."
            
            price_info = f"💰 **Recent AGMARKNET Market Prices for {crop_name.title()}**\n\n"
            price_info += f"📍 **Location:** {district_name if district_name else 'Various'}, {state_name.title()}\n\n"
            
            processed_records = 0
            for record in records:
                if processed_records >= 5:
                    break
                district = record.get('district', 'N/A')
                market = record.get('market', 'N/A')
                modal_price = record.get('modal_price', 'N/A')
                arrival_date = record.get('arrival_date', 'N/A')
                
                if modal_price and modal_price != '0':
                    price_info += f"**District:** {district}\n"
                    price_info += f"**Market:** {market}\n"
                    price_info += f"**Price:** ₹{modal_price}/Quintal\n"
                    if arrival_date != 'N/A':
                        price_info += f"**Date:** {arrival_date}\n"
                    price_info += "---\n"
                    processed_records += 1
            
            if processed_records == 0:
                return f"⚠️ No recent market price data (with valid prices) found for {crop_name.title()} in {state_name.title()}."
            return price_info
        else:
            return f"⚠️ No market price data found for {crop_name.title()} in {state_name.title()}."
            
    except requests.exceptions.RequestException as e:
        return f"⚠️ Could not fetch market prices due to a network issue: {str(e)}"
    except KeyError:
        return "⚠️ DATA_GOV_API_KEY not found. Please add it to your .env file."
    except Exception as e:
        print(f"Error in get_market_price_with_district: {e}")
        return f"⚠️ An error occurred while fetching market prices: {e}"

