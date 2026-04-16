
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def test_auth():
    SCOPE = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './secure_keys/my-service-account.json')
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    
    print(f"Testing with Credentials: {creds_path}")
    print(f"Testing with Sheet ID: {sheet_id}")
    
    try:
        creds = Credentials.from_service_account_file(
            creds_path,
            scopes=SCOPE
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        print(f"SUCCESS! Connected to sheet: {sheet.title}")
    except Exception as e:
        print(f"FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auth()
