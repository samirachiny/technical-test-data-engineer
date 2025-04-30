import requests
import os
import json
import logging
import time
import smtplib
from email.message import EmailMessage
from typing import Optional
from pydantic import ValidationError
from moovitamix_fastapi.classes_out import TracksOut, UsersOut, ListenHistoryOut
from moovitamix_fastapi.constants import *


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

# ==================== NOTIFICATION EMAIL ====================
def notify_failure(subject: str, body: str):
    """Envoie un email de notification en cas d'échec"""
    if not NOTIFY_EMAIL: 
        return
    
    msg = EmailMessage()
    msg.set_content(body)  
    msg['Subject'] = subject  
    msg['From'] = SMTP_USER 
    msg['To'] = DEST_EMAIL  
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SMTP_USER, SMTP_PASSWORD) 
            smtp.send_message(msg) 
        logging.info("Notification email envoyee.")
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi de l'email : {e}")

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
    notify_failure(
    f"[ERREUR] Pipeline Moov AI - {endpoint}",
    f"Le pipeline a échoué après {MAX_RETRIES} tentatives pour {endpoint}."
    )
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
