
import json
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

load_dotenv()

def try_fix_and_auth():
    creds_path = './secure_keys/my-service-account.json'
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    SCOPE = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    with open(creds_path, 'r') as f:
        data = json.load(f)
    
    pk = data.get('private_key', '')
    
    # Attempt 1: As is
    print("Trying Attempt 1: Original key")
    try:
        creds = Credentials.from_service_account_info(data, scopes=SCOPE)
        client = gspread.authorize(creds)
        client.open_by_key(sheet_id)
        print("SUCCESS with Original key!")
        return
    except Exception as e:
        print(f"Failed Attempt 1: {e}")

    # Attempt 2: Ensure real newlines
    print("\nTrying Attempt 2: Replacing \\n with actual newlines")
    fixed_pk = pk.replace('\\n', '\n')
    data['private_key'] = fixed_pk
    try:
        creds = Credentials.from_service_account_info(data, scopes=SCOPE)
        client = gspread.authorize(creds)
        client.open_by_key(sheet_id)
        print("SUCCESS with Fixed newlines!")
        return
    except Exception as e:
        print(f"Failed Attempt 2: {e}")

    # Attempt 3: Stripping whitespace
    print("\nTrying Attempt 3: Stripping whitespace from private_key")
    fixed_pk = pk.strip()
    data['private_key'] = fixed_pk
    try:
        creds = Credentials.from_service_account_info(data, scopes=SCOPE)
        client = gspread.authorize(creds)
        client.open_by_key(sheet_id)
        print("SUCCESS with Stripped key!")
        return
    except Exception as e:
        print(f"Failed Attempt 3: {e}")

if __name__ == "__main__":
    try_fix_and_auth()
