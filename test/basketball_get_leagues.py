import requests
import json
import os
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v1.basketball.api-sports.io"

def get_leagues():
    if not API_KEY:
        print("Error: API_FOOTBALL_KEY not found in .env")
        return

    url = f"{BASE_URL}/leagues"
    headers = {
        'x-apisports-key': API_KEY
    }
    
    print(f"Fetching data from {url}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Check for API-level errors
        if isinstance(data, dict) and data.get("errors"):
            print("API Error:", data["errors"])
            # Continue to save anyway to debug
            
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'basketball_leagues.json')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully saved data to {output_path}")
        if isinstance(data, dict) and "response" in data:
            print(f"Retrieved {len(data['response'])} leagues.")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if 'response' in locals():
            print(response.text)

if __name__ == "__main__":
    get_leagues()
