import os
import requests
import json

# 1. Get your credentials from environment variables
api_key = os.getenv("GOOGLE_API_KEY")
cse_id = os.getenv("GOOGLE_CSE_ID")

# 2. Set the search query
search_query = "latest news on electric vehicles"

# 3. Construct the API request URL
url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cse_id}&q={search_query}"

# 4. Make the request and get the response
try:
    response = requests.get(url)
    response.raise_for_status()  # Raises an exception for bad responses (4xx or 5xx)

    # 5. Parse the JSON data from the response
    search_results = response.json()

    # 6. Extract and print the useful information
    print(f"Found {search_results['searchInformation']['totalResults']} results.\n")

    # Loop through the first few results and print their title and link
    if 'items' in search_results:
        for item in search_results['items']:
            print(f"Title: {item['title']}")
            print(f"Link: {item['link']}\n")
    else:
        print("No items found.")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
except KeyError:
    # This can happen if the JSON response is an error message
    print("Could not parse the results. Check your credentials or query.")
    print("Response:", response.text)