# app.py
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import requests
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuration
NBA_DATA_BASE_URL = "https://data.nba.net"
NBA_STATS_BASE_URL = "https://stats.nba.com/stats"

# Constants for team IDs
TEAM_ID_MAP = {
    "ATL": 1610612737, "BOS": 1610612738, "BKN": 1610612751, "CHA": 1610612766,
    "CHI": 1610612741, "CLE": 1610612739, "DAL": 1610612742, "DEN": 1610612743,
    "DET": 1610612765, "GSW": 1610612744, "HOU": 1610612745, "IND": 1610612754,
    "LAC": 1610612746, "LAL": 1610612747, "MEM": 1610612763, "MIA": 1610612748,
    "MIL": 1610612749, "MIN": 1610612750, "NOP": 1610612740, "NYK": 1610612752,
    "OKC": 1610612760, "ORL": 1610612753, "PHI": 1610612755, "PHX": 1610612756,
    "POR": 1610612757, "SAC": 1610612758, "SAS": 1610612759, "TOR": 1610612761,
    "UTA": 1610612762, "WAS": 1610612764
}

# Cache for storing API responses to minimize requests
cache = {}
CACHE_EXPIRY = 3600  # Cache expiry in seconds

# Headers to mimic browser request for NBA Stats API
HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.nba.com/',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true'
}

# Model variables
model = None
model_features = None

def get_cached_response(url, headers=None, params=None):
    """Get response from cache or make a new request"""
    cache_key = url + str(params or {})
    
    if cache_key in cache:
        timestamp, data = cache[cache_key]
        if datetime.now().timestamp() - timestamp < CACHE_EXPIRY:
            return data
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    
    cache[cache_key] = (datetime.now().timestamp(), data)
    return data

def get_player_stats(player_id, season="2023-24"):
    """Get stats for a specific player"""
    endpoint = f"{NBA_STATS_BASE_URL}/playerprofilev2"
    params = {
        'PlayerID': player_id,
        'PerMode': 'PerGame',
        'SeasonType': 'Regular Season'
    }
    
    try:
        data = get_cached_response(endpoint, headers=HEADERS, params=params)
        return data
    except Exception as e:
        print(f"Error getting player stats: {e}")
        return None

def get_team_stats(team_id, season="2023-24"):
    """Get team stats"""
    endpoint = f"{NBA_STATS_BASE_URL}/teamdashboardbygeneralsplits"
    params = {
        'TeamID': team_id,
        'Season': season,
        'SeasonType': 'Regular Season',
        'MeasureType': 'Base',
        'PerMode': 'PerGame'
    }
    
    try:
        data = get_cached_response(endpoint, headers=HEADERS, params=params)
        return data
    except Exception as e:
        print(f"Error getting team stats: {e}")
        return None

def search_player(player_name):
    """Search for player by name"""
    endpoint = f"{NBA_STATS_BASE_URL}/playerindex"
    params = {
        'Season': '2023-24',
        'SeasonType': 'Regular Season',
        'LeagueID': '00'
    }
    
    try:
        data = get_cached_response(endpoint, headers=HEADERS, params=params)
        
        # Extract headers and rows from response
        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']
        
        # Convert to pandas DataFrame for easier filtering
        df = pd.DataFrame(rows, columns=headers)
        
        # Filter players by name (case insensitive partial match)
        matching_players = df[df['PLAYER_NAME'].str.lower().str.contains(player_name.lower())]
        
        if matching_players.empty:
            return []
        
        # Return list of matching players with relevant info
        result = matching_players[['PERSON_ID', 'PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION']].to_dict('records')
        return result
    
    except Exception as e:
        print(f"Error searching player: {e}")
        return []

def train_prediction_model():
    """Train a model to predict game outcomes"""
    global model, model_features
        # In a real application, we would load historical game data
    # For demonstration, we'll create sample data
    
    # Features that predict game outcomes
    features = [
        'team_pts', 'team_ast', 'team_reb', 'team_stl', 'team_blk', 
        'team_fg_pct', 'team_ft_pct', 'team_3p_pct',
        'opp_pts', 'opp_ast', 'opp_reb', 'opp_stl', 'opp_blk',
        'opp_fg_pct', 'opp_ft_pct', 'opp_3p_pct'
    ]
    
    model_features = features
    
    # For demonstration, we'll simulate having historical data
    np.random.seed(42)
    n_samples = 1000
    X = np.random.rand(n_samples, len(features))
    
    # Simulate target (win/loss) based on synthetic feature importance
    # Higher scoring and shooting percentage increases win probability
    weights = np.array([0.2, 0.1, 0.1, 0.05, 0.05, 0.15, 0.1, 0.1, 
                        -0.15, -0.05, -0.05, -0.05, -0.05, -0.1, -0.05, -0.05])
    y_proba = np.dot(X, weights) + np.random.normal(0, 0.1, n_samples)    y = (y_proba > 0).astype(int)
    
    # Train a Random Forest Classifier
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return {"message": "Model trained successfully"}

def get_team_features(team_abbr, opponent_abbr):
    """Get features for prediction model input"""
    # Get team IDs
    team_id = TEAM_ID_MAP.get(team_abbr.upper())
    opponent_id = TEAM_ID_MAP.get(opponent_abbr.upper())
    
    if not team_id or not opponent_id:
        return None, "Invalid team abbreviation"
    
    try:
        # Get team stats
        team_data = get_team_stats(team_id)
        opp_data = get_team_stats(opponent_id)
        
        if not team_data or not opp_data:
            return None, "Could not retrieve team data"        
        # Extract relevant stats from team data
        team_stats = team_data['resultSets'][0]['rowSet'][0]
        headers = team_data['resultSets'][0]['headers']
        team_df = pd.DataFrame([team_stats], columns=headers)
        
        # Extract relevant stats from opponent data
        opp_stats = opp_data['resultSets'][0]['rowSet'][0]
        opp_df = pd.DataFrame([opp_stats], columns=headers)
        
        # Create feature vector
        features = {
            'team_pts': team_df['PTS'].values[0],
            'team_ast': team_df['AST'].values[0],
            'team_reb': team_df['REB'].values[0],
            'team_stl': team_df['STL'].values[0],
            'team_blk': team_df['BLK'].values[0],
            'team_fg_pct': team_df['FG_PCT'].values[0],
            'team_ft_pct': team_df['F