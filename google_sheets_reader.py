import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
from urllib.parse import urlparse

class GoogleSheetsReader:
    # Classe pour lire les données depuis Google Sheets.
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    def __init__(self, sheet_url, credentials_path):
        self.sheet_url = sheet_url
        self.credentials_path = credentials_path
        self.sheet = self._connect_to_sheet()

    def _connect_to_sheet(self):
        # Établit la connexion à Google Sheets.
        creds = self._load_credentials()
        client = gspread.authorize(creds)
        sheet_id = self._extract_sheet_id(self.sheet_url)
        return client.open_by_key(sheet_id).sheet1

    def _load_credentials(self):
        # Charge ou génère les credentials OAuth.
        creds = None
        token_path = 'token.pickle'

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

        return creds

    def _extract_sheet_id(self, url):
        # Extrait l'identifiant de la feuille depuis l'URL.
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        return path_parts[3] if len(path_parts) > 3 else None

    def get_active_players(self):
        # Récupère la liste des joueurs actifs depuis la feuille.
        cell_range = self.sheet.range('B13:B22')
        return [cell.value.strip() for cell in cell_range if cell.value.strip()]