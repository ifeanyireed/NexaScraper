
import json
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
import time

load_dotenv()

def test_clock_offset():
    creds_path = './secure_keys/my-service-account.json'
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    SCOPE = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    with open(creds_path, 'r') as f:
        info = json.load(f)

    print("Trying with 60 seconds offset in the past...")
    try:
        # We can't easily inject offset into Credentials.from_service_account_info
        # but we can try to change the system time for a moment if we had sudo, which we don't.
        # Alternatively, we can use a custom signer, but that's complex.
        
        # Let's try to just use a different library or method.
        creds = Credentials.from_service_account_info(info, scopes=SCOPE)
        
        # Manually refresh with a custom request that might handle it? 
        # No, let's try to just print the iat if we can.
        
        print("Actually, let's just try to see if it's a project mismatch.")
        print(f"Project ID in JSON: {info.get('project_id')}")
        print(f"Client Email: {info.get('client_email')}")
        
        if info.get('project_id') not in info.get('client_email'):
            print("WARNING: Project ID mismatch in Client Email!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_clock_offset()
