import requests
import json
import os
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v1.basketball.api-sports.io"

def get_h2h(home_id, away_id, season=None, timezone="UTC"):
    if not API_KEY:
        print("Error: API_FOOTBALL_KEY not found in .env")
        return

    if not home_id or not away_id:
        print("Error: Both home_id and away_id are required")
        return

    url = f"{BASE_URL}/games"
    headers = {
        'x-apisports-key': API_KEY
    }
    
    h2h_param = f"{home_id}-{away_id}"
    
    params = {
        'h2h': h2h_param,
        'timezone': timezone
    }
    
    if season:
        params['season'] = season
    
    print(f"Fetching H2H games for Home ID: {home_id}, Away ID: {away_id}, Season: {season}, Timezone: {timezone}...")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Check for API-level errors
        if isinstance(data, dict) and data.get("errors"):
            print("API Error:", data["errors"])
            
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        season_str = f"_season_{season}" if season else ""
        filename = f'basketball_h2h_{home_id}_{away_id}{season_str}.json'
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully saved data to {output_path}")
        if isinstance(data, dict) and "response" in data:
            print(f"Retrieved {len(data['response'])} H2H games.")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if 'response' in locals():
            print(response.text)

if __name__ == "__main__":
    # Example usage: 
    # Philadelphia 76ers (154) vs Golden State Warriors (141)
    home_team = 154
    away_team = 141
    target_season = "2025-2026"
    get_h2h(home_id=home_team, away_id=away_team, season=target_season)
