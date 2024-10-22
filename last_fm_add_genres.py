import requests
import unicodedata
import pandas as pd
import time
import logging
import os
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv('API_KEY')
API_URL = "http://ws.audioscrobbler.com/2.0/"
RETRY_DELAY = 5  # 5 minutes in seconds
MAX_RETRIES = 2    # Maximum number of retries before giving up

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("artist_info.log"),
        logging.StreamHandler()
    ]
)

if API_KEY:
    logging.info("API_KEY present")

def is_latin(s):
    for ch in s:
        if ch.isalpha():
            # Get the script property of the character
            try:
                script = unicodedata.name(ch).split(' ')[0]
                if script != 'LATIN':
                    return False
            except ValueError:
                # Character does not have a Unicode name
                return False
        else:
            # Ignore non-alphabetic characters (spaces, punctuation, numbers)
            continue
    return True

def get_artist_info(artist_name):
    if not is_latin(artist_name):
        logging.info(f"Skipping artist '{artist_name}' because it contains non-Latin characters.")
        return None

    params = {
        'method': 'artist.getinfo',
        'artist': artist_name,
        'api_key': API_KEY,
        'format': 'json'
    }
    attempt = 0
    while attempt < MAX_RETRIES:
        try:            
            response = requests.get(API_URL, params=params)
            logging.info(f"API INFO>>>> '{API_URL}' and response '{response.json()}'")
            if response.status_code == 200:
                data = response.json()
                if 'artist' in data:
                    artist_info = data['artist']
                    genres = [tag['name'] for tag in artist_info.get('tags', {}).get('tag', [])]
                    if not genres:
                        genres = ['Unknown genre']
                    return {
                        'name': artist_info['name'],
                        'genres': genres,
                        'country': artist_info.get('country', 'Unknown')
                    }
                else:
                    logging.warning(f"Artist '{artist_name}' not found in the response.")
                    return None
            elif response.status_code == 429:
                # Rate limiting encountered
                logging.warning(f"Rate limit reached. Waiting for {RETRY_DELAY} seconds before retrying...")
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Error {response.status_code} while fetching data for artist '{artist_name}'.")
                time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            logging.error(f"Request exception for artist '{artist_name}': {e}")
            logging.info(f"Waiting for {RETRY_DELAY} seconds before retrying...")
            time.sleep(RETRY_DELAY)
        attempt += 1
        logging.info(f"Retrying ({attempt}/{MAX_RETRIES}) for artist '{artist_name}'...")
    return None

# Go through each artist and update the 'Genres' in the DataFrame

def enter_genres(tracks):
    songs = pd.DataFrame(tracks)
    artist_name_df=songs['Artist']
    artist_name_list = artist_name_df.tolist()
    for artist in artist_name_list:
        time.sleep(1)
        artist_data = get_artist_info(artist)
        if artist_data:
            genres_str = ', '.join(artist_data['genres'])  # Join the genres into a single string
            logging.info(f"Updating genres for artist: {artist_data['name']}") 
            logging.info(f"Genres: {genres_str}")
            songs.loc[songs['Artist'] == artist, 'Genres'] = genres_str 
        else:
            logging.info(f"Artist '{artist}' not found or data unavailable.\n")
    return songs


