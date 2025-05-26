#!/usr/bin/env python3
"""
Script to test the full transcription flow including Google Sheets integration
"""
import json
import base64
import requests
from datetime import datetime

def test_server_and_sheets():
    print("\n🔍 Testing Flask Server and Google Sheets Integration")
    print("=" * 60)
    
    # 1. Test server connection
    try:
        response = requests.get("http://localhost:8000")
        if response.status_code == 200:
            print("✓ Server is running")
        else:
            print(f"❌ Server returned unexpected status: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running on port 8000")
        print("Please start the Flask server first!")
        return
    
    # 2. Test file upload with explicit Google Sheets request
    test_file = "/workspaces/codespaces-flask/audio files/video (4).mp4"
    print(f"\n📂 Testing with file: {test_file}")
    
    try:
        with open(test_file, 'rb') as f:
            file_data = f.read()
            file_data_b64 = base64.b64encode(file_data).decode('utf-8')
        
        payload = {
            'file_data': file_data_b64,
            'file_name': 'video (4).mp4',
            'debug': True,
            'skip_google_sheets': False
        }
        
        print("\n🚀 Sending transcription request...")
        response = requests.post(
            "http://localhost:8000/transcribe",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Transcription Result:")
            print("-" * 40)
            print(result.get('transcription', 'No transcription found'))
            print("-" * 40)
            
            if 'sheet_status' in result:
                print(f"\n📝 Google Sheets Status: {result['sheet_status']}")
        else:
            print(f"\n❌ Error Response: {response.text}")
    
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        
if __name__ == "__main__":
    test_server_and_sheets()
