
import json
import os
from pathlib import Path

def validate_key():
    creds_path = './secure_keys/my-service-account.json'
    if not os.path.exists(creds_path):
        print(f"Error: {creds_path} not found")
        return

    with open(creds_path, 'r') as f:
        try:
            data = json.load(f)
            print("✓ JSON is valid")
        except Exception as e:
            print(f"✗ JSON is INVALID: {e}")
            return

    pk = data.get('private_key', '')
    if not pk:
        print("✗ No private_key field found")
        return
    
    print(f"✓ private_key length: {len(pk)}")

    if "-----BEGIN PRIVATE KEY-----" not in pk:
        print("✗ Header missing in private_key")
    if "-----END PRIVATE KEY-----" not in pk:
        print("✗ Footer missing in private_key")
    
    # Check for literal \n vs real newlines
    if "\\n" in pk:
        print("✓ private_key contains '\\n' literals (Correct for JSON)")
    else:
        print("! private_key does not contain '\\n' literals (Maybe it has real newlines?)")

    # Check for trailing spaces
    lines = pk.split("\\n")
    has_trailing_space = any(line.endswith(" ") for line in lines)
    if has_trailing_space:
        print("✗ Found trailing spaces in private_key lines")
    else:
        print("✓ No trailing spaces found in private_key lines")

if __name__ == "__main__":
    validate_key()
