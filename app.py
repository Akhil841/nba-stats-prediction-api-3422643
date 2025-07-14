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

def get_player_stats(player_id, season="2023-24