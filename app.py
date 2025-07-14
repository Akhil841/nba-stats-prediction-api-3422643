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

# Con