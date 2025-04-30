import requests
import os
import json
import logging
import time
from typing import Optional
from pydantic import ValidationError
from moovitamix_fastapi.classes_out import TracksOut, UsersOut, ListenHistoryOut

# ------------------- CONFIGURATION -------------------
API_URL = "http://127.0.0.1:8000"
ENDPOINTS = ["tracks", "users", "listen_history"]
DATA_DIR = "data"
MAX_RETRIES = 3
TIMEOUT = 10  # secondes


# ------------------- LOGGING -------------------
logging.basicConfig(
    filename='data_pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ------------------- SCHÉMAS -------------------
SCHEMA_BY_ENDPOINT = {
    "tracks": TracksOut,
    "users": UsersOut,
    "listen_history": ListenHistoryOut
}

# ------------------- FONCTIONS -------------------
def fetch_data(endpoint: str) -> Optional[dict]:
    url = f"{API_URL}/{endpoint}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            logging.info(f"[{endpoint}] Donnees recuperees avec succes.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.warning(f"[{endpoint}] Echec tentative {attempt} - {e}")
            time.sleep(2 * attempt)
    logging.error(f"[{endpoint}] Echec apres {MAX_RETRIES} tentatives.")
    notify_failure(f"[ERREUR] Pipeline Moov AI - {endpoint}",
                   f"Le pipeline a echoue apres {MAX_RETRIES} tentatives pour {endpoint}.")
    return None

def validate_items(endpoint: str, data: dict) -> bool:
    schema = SCHEMA_BY_ENDPOINT[endpoint]
    try:
        for item in data.get("items", []):
            schema(**item)
        return True
    except ValidationError as e:
        logging.error(f"[{endpoint}] Erreur de validation : {e}")
        notify_failure(f"[ERREUR] Validation - {endpoint}", str(e))
        return False

def save_to_json(data: dict, filename: str):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"[{filename}] Donnees sauvegardees.")
    except Exception as e:
        logging.error(f"[{filename}] Erreur lors de la sauvegarde : {e}")
        notify_failure(f"[ERREUR] Sauvegarde - {filename}", str(e))

# ------------------- MAIN -------------------
def main():
    logging.info("Debut du pipeline d'ingestion Moov AI")
    for endpoint in ENDPOINTS:
        data = fetch_data(endpoint)
        if data and validate_items(endpoint, data):
            save_to_json(data, f"{endpoint}.json")
        else:
            logging.error(f"[{endpoint}] Donnees ignorees en raison d'une erreur.")
    logging.info("Fin du pipeline d'ingestion Moov AI")

if __name__ == "__main__":
    main()
