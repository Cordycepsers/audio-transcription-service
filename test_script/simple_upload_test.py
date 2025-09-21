#!/usr/bin/env python3
"""
Simple file upload test for Flask transcription app
"""
import requests
import base64
import os

def upload_small_file():
    """Upload the smallest video file for testing"""
    
    # Use the smallest video file
    file_path = "/workspaces/codespaces-flask/audio files/video (4).mp4"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    print(f"📁 Reading file: {os.path.basename(file_path)}")
    print(f"📊 File size: {os.path.getsize(file_path)} bytes")
    
    # Read and encode file
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_data_b64 = base64.b64encode(file_data).decode('utf-8')
        
        payload = {
            'file_data': file_data_b64,
            'file_name': os.path.basename(file_path)
        }
        
        print("🚀 Uploading to transcription service...")
        print("⏳ This may take a few minutes...")
        
        response = requests.post(
            'http://localhost:8000/transcribe',
            json=payload,
            timeout=300  # 5 minutes
        )
        
        print(f"📬 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Transcription completed.")
            print("\n📝 Transcription:")
            print("-" * 50)
            print(result.get('transcription', 'No transcription found'))
            print("-" * 50)
            
            if 'metadata' in result:
                print(f"\n📊 Metadata: {result['metadata']}")
                
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    upload_small_file()
