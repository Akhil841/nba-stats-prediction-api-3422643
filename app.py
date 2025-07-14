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
    "CHI": 1610612741, "CLE": 1610