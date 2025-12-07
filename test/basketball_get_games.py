import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v1.basketball.api-sports.io"

def get_games(league_id=12, date=None, season=None, timezone="UTC"):
    if not API_KEY:
        print("Error: API_FOOTBALL_KEY not found in .env")
        return

    if date is None and season is None:
        # Default to today's date if not provided
        date = datetime.now().strftime("%Y-%m-%d")

    url = f"{BASE_URL}/games"
    headers = {
        'x-apisports-key': API_KEY
    }
    params = {
        'league': league_id,
        'timezone': timezone
    }
    
    if date:
        params['date'] = date
    if season:
        params['season'] = season
    
    print(f"Fetching games for League ID: {league_id}, Date: {date}, Season: {season}, Timezone: {timezone}...")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Check for API-level errors
        if isinstance(data, dict) and data.get("errors"):
            print("API Error:", data["errors"])
            
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f'basketball_games_league_{league_id}_{season or date}.json'
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully saved data to {output_path}")
        if isinstance(data, dict) and "response" in data:
            print(f"Retrieved {len(data['response'])} games.")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if 'response' in locals():
            print(response.text)

if __name__ == "__main__":
    # Example usage: Get NBA (League 12) games for season 2025-2026
    # Note: API requires 'season' OR 'date' usually, but checking docs it seems we can use season
    target_season = "2025-2026"
    target_date = "2025-12-06"
    get_games(league_id=12, season=target_season, date=target_date, timezone="UTC")
