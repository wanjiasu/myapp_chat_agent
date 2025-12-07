import requests
import json
import os
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v1.basketball.api-sports.io"

def get_odds(league_id=None, season=None, date=None, game_id=None, bookmaker_id=None, bet_id=None):
    if not API_KEY:
        print("Error: API_FOOTBALL_KEY not found in .env")
        return

    # Basic validation: At least one major filter usually required, but let's rely on API response
    if not any([league_id, date, game_id]):
        print("Warning: It is recommended to provide at least league_id, date, or game_id.")

    url = f"{BASE_URL}/odds"
    headers = {
        'x-apisports-key': API_KEY
    }
    
    params = {}
    if league_id:
        params['league'] = league_id
    if season:
        params['season'] = season
    # 'date' parameter is not supported by the odds endpoint based on API response
    # if date:
    #     params['date'] = date
    if game_id:
        params['game'] = game_id
    if bookmaker_id:
        params['bookmaker'] = bookmaker_id
    if bet_id:
        params['bet'] = bet_id
        
    print(f"Fetching odds with params: {params}...")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Check for API-level errors
        if isinstance(data, dict) and data.get("errors"):
            print("API Error:", data["errors"])
            
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Construct filename
        parts = []
        if league_id: parts.append(f"league_{league_id}")
        if season: parts.append(f"season_{season}")
        if date: parts.append(f"date_{date}")
        if game_id: parts.append(f"game_{game_id}")
        
        filename_suffix = "_".join(parts) if parts else "all"
        filename = f'basketball_odds_{filename_suffix}.json'
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully saved data to {output_path}")
        if isinstance(data, dict) and "response" in data:
            print(f"Retrieved {len(data['response'])} odds entries.")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if 'response' in locals():
            print(response.text)

if __name__ == "__main__":
    # Example usage: Get Odds for a specific game
    # Using Game ID from previous fetch (Philadelphia 76ers vs Golden State Warriors on 2025-12-05)
    # ID: 469803
    target_game_id = 469803
    get_odds(game_id=target_game_id)
