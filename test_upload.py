#!/usr/bin/env python3
"""
Test script to upload audio/video files to the Flask transcription app
"""
import requests
import os
import json
import base64

def test_file_upload(file_path, server_url="http://localhost:8000"):
    """
    Test uploading a file to the transcription endpoint
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return False
    
    print(f"Testing upload of: {file_path}")
    print(f"File size: {os.path.getsize(file_path)} bytes")
    
    try:
        # Read and encode the file as base64
        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_data_b64 = base64.b64encode(file_data).decode('utf-8')
        
        # Prepare JSON payload as expected by the Flask endpoint
        payload = {
            'file_data': file_data_b64,
            'file_name': os.path.basename(file_path),
            'mime_type': 'video/mp4'
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        print("Uploading file to /transcribe endpoint...")
        response = requests.post(f"{server_url}/transcribe", 
                               json=payload, 
                               headers=headers, 
                               timeout=300)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Upload successful!")
                print(f"Transcription: {result.get('transcription', 'No transcription found')}")
                print(f"Metadata: {result.get('metadata', {})}")
                return True
            except json.JSONDecodeError:
                print("✅ Upload successful, but response is not JSON:")
                print(response.text[:500])
                return True
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main test function"""
    print("🎬 Flask Audio Transcription Upload Test")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding correctly")
            return
        print("✅ Server is running")
    except:
        print("❌ Server is not running on localhost:8000")
        print("Please make sure the Flask app is running first!")
        return
    
    # Test files available
    audio_files_dir = "/workspaces/codespaces-flask/audio files"
    test_files = [
        os.path.join(audio_files_dir, "video (2).mp4"),
        os.path.join(audio_files_dir, "video (3).mp4"),
        os.path.join(audio_files_dir, "video (4).mp4"),
        os.path.join(audio_files_dir, "video (5).mp4")
    ]
    
    print(f"\nFound {len(test_files)} test files:")
    for i, file_path in enumerate(test_files, 1):
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"  {i}. {os.path.basename(file_path)} ({size_mb:.2f} MB)")
        else:
            print(f"  {i}. {os.path.basename(file_path)} (NOT FOUND)")
    
    # Test with the smallest file first
    valid_files = [f for f in test_files if os.path.exists(f)]
    if not valid_files:
        print("❌ No valid test files found")
        return
    
    # Sort by file size and test the smallest one first
    valid_files.sort(key=lambda x: os.path.getsize(x))
    smallest_file = valid_files[0]
    
    print(f"\n🔄 Testing with smallest file: {os.path.basename(smallest_file)}")
    print("-" * 50)
    
    success = test_file_upload(smallest_file)
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
        print("\nTroubleshooting tips:")
        print("1. Make sure the Flask server is running")
        print("2. Check if the required dependencies are installed")
        print("3. Verify the upload endpoint is working")
        print("4. Check server logs for any errors")

if __name__ == "__main__":
    main()
