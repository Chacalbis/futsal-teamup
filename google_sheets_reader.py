import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
from urllib.parse import urlparse
from datetime import datetime

def get_google_sheet(sheet_url, credentials_path):
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    creds = None
    # Le fichier token.pickle stocke les jetons d'accès et d'actualisation de l'utilisateur
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # Si aucun jeton valide n'existe, l'utilisateur doit se connecter.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Enregistrer les jetons pour la prochaine exécution
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    client = gspread.authorize(creds)
    
    # Extraire l'identifiant de la feuille à partir de l'URL
    sheet_id = extract_sheet_id(sheet_url)
    return client.open_by_key(sheet_id).sheet1

def extract_sheet_id(sheet_url):
    # Extraire l'identifiant de la feuille à partir de l'URL
    parsed_url = urlparse(sheet_url)
    path_parts = parsed_url.path.split('/')
    return path_parts[3] if len(path_parts) > 3 else None

def load_active_players_from_sheets(sheet):
    cell_range = sheet.range('B13:B22')
    active_players = []
    
    for cell in cell_range:
        if cell.value.strip():  # Vérifie que la cellule n'est pas vide
            active_players.append(cell.value.strip())

    return active_players

def get_active_players(sheet_url, credentials_path):
    sheet = get_google_sheet(sheet_url, credentials_path)
    return load_active_players_from_sheets(sheet)
