# NBA Stats and Prediction API

A Python HTTP server that handles GET and POST requests to retrieve NBA player stats and predict game outcomes based on team statistics.

## Features

- Player search by name
- Retrieve player statistics
- Retrieve team statistics
- Predict win probability for games between two teams

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the server:
   ```
   python app.py
   ```

## API Endpoints

### GET /
Returns available endpoints and API information

### GET /player/search/{name}
Search for players by name

### GET /player/{player_id}/stats
Get st