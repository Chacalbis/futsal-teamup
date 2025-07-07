import gspread
from google.oauth2.service_account import Credentials
from urllib.parse import urlparse
from datetime import datetime

class GoogleSheetsReader:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, sheet_url, credentials_path):
        self.sheet_url = sheet_url
        self.credentials_path = credentials_path
        self.sheet = self._connect_to_sheet()

    def _connect_to_sheet(self):
        # Connexion à Google Sheets
        creds = self._load_credentials()
        client = gspread.authorize(creds)
        sheet_id = self._extract_sheet_id(self.sheet_url)
        return client.open_by_key(sheet_id).sheet1

    def _load_credentials(self):
        # Utilisation du compte de service
        return Credentials.from_service_account_file(self.credentials_path, scopes=self.SCOPES)

    def _extract_sheet_id(self, url):
        # Extraction de l'identifiant de la feuille
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        return path_parts[3] if len(path_parts) > 3 else None

    def get_active_players(self):
        # Récupération de la liste des joueurs actifs
        cell_range = self.sheet.range('B13:B22')
        return [cell.value.strip() for cell in cell_range if cell.value.strip()]

    def save_match_result(self, teams):
        # Enregistre le tirage des équipes dans l'onglet Tirages.
        spreadsheet = self.sheet.spreadsheet
        try:
            worksheet = spreadsheet.worksheet("Tirages")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title="Tirages", rows=100, cols=5)
            worksheet.append_row(["ID Match", "Date", "Équipe 1", "Équipe 2", "Diff de buts (par rapport à équipe 1)"])

        match_ids = worksheet.col_values(1)[1:]  # Ignore l'en-tête
        match_id = max([int(x) for x in match_ids] + [0]) + 1 if match_ids else 1

        date = datetime.now().strftime("%d/%m/%Y")
        team1_players = ",".join(p.name for p in teams[0].players)
        team2_players = ",".join(p.name for p in teams[1].players)

        worksheet.append_row([str(match_id), date, team1_players, team2_players, ""])