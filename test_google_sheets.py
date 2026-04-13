#!/usr/bin/env python3
"""
Quick verification script for Google Sheets integration.
Run this to test your setup before running the full scraper.
"""

import sys
import os
from pathlib import Path

def check_environment():
    """Check if environment variables are set."""
    print("\n📋 Checking Environment Variables...")
    
    sheet_id = os.getenv('SHEET_ID')
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not sheet_id:
        print("❌ SHEET_ID not set in .env")
        return False
    else:
        print(f"✓ SHEET_ID: {sheet_id[:20]}...")
    
    if not creds_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set in .env")
        return False
    else:
        print(f"✓ Credentials path: {creds_path}")
    
    return True


def check_credentials_file():
    """Check if service account JSON exists and is valid."""
    print("\n📁 Checking Service Account File...")
    
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './secure_keys/my-service-account.json')
    
    if not Path(creds_path).exists():
        print(f"❌ Service account file not found: {creds_path}")
        return False
    
    print(f"✓ File exists: {creds_path}")
    
    # Check if it's valid JSON
    try:
        import json
        with open(creds_path) as f:
            creds = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key_id', 'client_email']
        for field in required_fields:
            if field not in creds:
                print(f"❌ Missing field in JSON: {field}")
                return False
        
        print(f"✓ Valid service account JSON")
        print(f"  - Project: {creds.get('project_id')}")
        print(f"  - Service Account: {creds.get('client_email')}")
        
        return True
    
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in {creds_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False


def check_imports():
    """Check if required packages are installed."""
    print("\n📦 Checking Required Packages...")
    
    packages = ['gspread', 'google', 'google.oauth2', 'google.oauth2.service_account']
    
    for package in packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} not installed")
            print(f"   Run: pip install -r requirements.txt")
            return False
    
    return True


def test_google_sheets_connection():
    """Test actual connection to Google Sheets."""
    print("\n🔗 Testing Google Sheets Connection...")
    
    try:
        from utils.google_sheets_writer import GoogleSheetsIntegration
        
        print("  Authenticating...")
        gs = GoogleSheetsIntegration()
        
        print("✓ Successfully connected to Google Sheets!")
        
        # Try to create test worksheet
        try:
            test_ws = gs.writer.create_worksheet("Test_Connection")
            print(f"✓ Can create worksheets")
            
            # Try to write a single test row
            test_data = [
                ["Status", "Message"],
                ["OK", "Google Sheets integration working!"]
            ]
            gs.writer._worksheet = test_ws
            test_ws.update(test_data)
            print(f"✓ Can write to worksheets")
            
        except Exception as e:
            print(f"⚠ Can connect but cannot write: {e}")
            return False
        
        return True
    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"\n   Troubleshooting:")
        print(f"   1. Verify SHEET_ID is correct (from Google Sheet URL)")
        print(f"   2. Check service account email has access to sheet")
        print(f"   3. Ensure APIs are enabled (Sheets + Drive)")
        print(f"   4. Verify credentials file path is correct")
        return False


def check_google_sheet_sharing():
    """Provide instructions on sharing Google Sheet with service account."""
    print("\n👥 Google Sheet Sharing (Manual Step)...")
    
    try:
        import json
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        with open(creds_path) as f:
            creds = json.load(f)
        
        service_email = creds.get('client_email', 'not-found')
        
        print(f"\n⚠️  Important: Share your Google Sheet with this email:")
        print(f"\n   {service_email}")
        print(f"\nSteps:")
        print(f"  1. Open https://docs.google.com/spreadsheets/d/{os.getenv('SHEET_ID')}")
        print(f"  2. Click 'Share' button (top right)")
        print(f"  3. Paste the email above")
        print(f"  4. Select 'Editor' permission")
        print(f"  5. Click 'Share'")
        print(f"\nIf not already done, this is why you're getting permission errors.")
        
    except Exception as e:
        print(f"Could not read service account email: {e}")


def main():
    """Run all checks."""
    print("=" * 60)
    print("Google Sheets Integration - Verification Check")
    print("=" * 60)
    
    checks = [
        ("Environment Variables", check_environment),
        ("Credentials File", check_credentials_file),
        ("Python Packages", check_imports),
        ("Google Sheets Connection", test_google_sheets_connection),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} - Unexpected error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All checks passed! Google Sheets integration is ready.")
        print("\nYou can now run:")
        print("  python main_scraper.py test")
        print("  (Results will be exported to Google Sheets)")
    else:
        print("\n⚠️  Some checks failed. Please fix issues above.")
        check_google_sheet_sharing()
        print("\nFor detailed setup, see: GOOGLE_SHEETS_SETUP.md")
    
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
