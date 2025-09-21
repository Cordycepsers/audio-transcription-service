#!/usr/bin/env python3
"""
Heroku Environment Setup Script
Handles Google Service Account key encoding and environment variable setup
"""

import os
import json
import base64
import subprocess
import sys

def encode_service_account_key(key_file_path):
    """Encode service account JSON key to base64 for Heroku"""
    try:
        with open(key_file_path, 'r') as f:
            key_data = json.load(f)
        
        # Convert to JSON string and encode to base64
        key_json = json.dumps(key_data, separators=(',', ':'))
        key_base64 = base64.b64encode(key_json.encode()).decode()
        
        return key_base64, key_data.get('client_email', 'unknown')
    except Exception as e:
        print(f"❌ Error encoding service account key: {e}")
        return None, None

def set_heroku_config(app_name, config_vars):
    """Set Heroku config variables"""
    success_count = 0
    total_count = len(config_vars)
    
    for key, value in config_vars.items():
        try:
            cmd = ['heroku', 'config:set', f'{key}={value}']
            if app_name:
                cmd.extend(['-a', app_name])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Set {key}")
                success_count += 1
            else:
                print(f"❌ Failed to set {key}: {result.stderr}")
        except Exception as e:
            print(f"❌ Error setting {key}: {e}")
    
    return success_count, total_count

def main():
    print("🚀 Heroku Environment Setup for Audio Transcription Service")
    print("=" * 60)
    
    # Check if Heroku CLI is installed
    try:
        subprocess.run(['heroku', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Heroku CLI not found. Please install it first:")
        print("   https://devcenter.heroku.com/articles/heroku-cli")
        sys.exit(1)
    
    # Get app name
    app_name = input("Enter your Heroku app name (or press Enter for default): ").strip()
    if not app_name:
        app_name = None
        print("Using default Heroku app")
    
    # Check for service account key
    key_file = 'service-account.json'
    if not os.path.exists(key_file):
        print(f"❌ Service account key file '{key_file}' not found")
        print("Please ensure the file exists in the current directory")
        sys.exit(1)
    
    # Encode service account key
    print(f"🔐 Encoding service account key from {key_file}...")
    key_base64, service_email = encode_service_account_key(key_file)
    
    if not key_base64:
        sys.exit(1)
    
    print(f"✅ Service account encoded: {service_email}")
    
    # Get configuration from user
    print("\n📝 Please provide the following configuration:")
    
    google_sheet_id = input("Google Sheet ID: ").strip()
    if not google_sheet_id:
        print("❌ Google Sheet ID is required")
        sys.exit(1)
    
    worksheet_name = input("Worksheet name (default: TRANSCRIPT FINAL): ").strip()
    if not worksheet_name:
        worksheet_name = "TRANSCRIPT FINAL"
    
    sentry_dsn = input("Sentry DSN (optional, press Enter to skip): ").strip()
    
    # Prepare config variables
    config_vars = {
        'FLASK_ENV': 'production',
        'GOOGLE_SHEET_ID': google_sheet_id,
        'GOOGLE_WORKSHEET_NAME': worksheet_name,
        'SERVICE_ACCOUNT_EMAIL': service_email,
        'GOOGLE_SERVICE_ACCOUNT_KEY': key_base64,
        'MAX_CONTENT_LENGTH': '104857600'  # 100MB
    }
    
    if sentry_dsn:
        config_vars['SENTRY_DSN'] = sentry_dsn
    
    # Set Heroku config variables
    print(f"\n🔧 Setting Heroku config variables...")
    success_count, total_count = set_heroku_config(app_name, config_vars)
    
    print(f"\n📊 Configuration Summary:")
    print(f"   ✅ Successfully set: {success_count}/{total_count} variables")
    
    if success_count == total_count:
        print("\n🎉 Heroku environment setup complete!")
        print("\nNext steps:")
        print("1. Deploy your app: git push heroku main")
        print("2. Scale your app: heroku ps:scale web=1")
        print("3. Check logs: heroku logs --tail")
        print("4. Test health: curl https://your-app.herokuapp.com/health")
    else:
        print(f"\n⚠️  Some variables failed to set. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
