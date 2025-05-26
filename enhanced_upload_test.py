#!/usr/bin/env python3
"""
Enhanced upload test for Flask transcription application
"""
import requests
import os
import base64
import time

def test_upload(file_path, server_url="http://localhost:8000"):
    """Test uploading a file and validate the transcription"""
    if not os.path.exists(file_path):
        print("❌ Error: File not found")
        return False

    print(f"\n📁 Reading file: {os.path.basename(file_path)}")
    print(f"📊 File size: {os.path.getsize(file_path) / 1024 / 1024:.2f} MB")

    try:
        # Read and encode file
        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_data_b64 = base64.b64encode(file_data).decode('utf-8')

        # Prepare request with Google Sheets enabled
        payload = {
            'file_data': file_data_b64,
            'file_name': os.path.basename(file_path),
            'skip_google_sheets': False,  # Enable Google Sheets integration
            'force_sheets_update': True  # Force Google Sheets update

        print("\n🚀 Uploading to transcription service...")
        response = requests.post(
            f"{server_url}/transcribe",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )

        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'transcription' in result:
                print("\n✅ Transcription successful!")
                print("\n📝 Transcription Result:")
                print("=" * 50)
                print(result['transcription'])
                print("=" * 50)

                # Validate transcription result
                if len(result['transcription']) > 0:
                    print("\n🔍 Validation:")
                    print("  ✓ Transcription not empty")
                    if any(c.isalpha() for c in result['transcription']):
                        print("  ✓ Contains alphabetic characters")
                    else:
                        print("  ⚠️ Warning: No alphabetic characters found")
                    
                    words = len(result['transcription'].split())
                    print(f"  ℹ Word count: {words}")
                    
                    if 'metadata' in result:
                        print("\n📊 Additional Metadata:")
                        for key, value in result['metadata'].items():
                            print(f"  • {key}: {value}")
                    
                    return True
                else:
                    print("\n⚠️ Warning: Empty transcription result")
                    return False
            else:
                print("\n❌ Error: No transcription in response")
                print(f"Response content: {response.text[:500]}")
                return False
        else:
            print(f"\n❌ Upload failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False

    except requests.Timeout:
        print("\n❌ Error: Request timed out")
        print("The server is taking too long to respond")
        return False
    except requests.RequestException as e:
        print(f"\n❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def main():
    """Main test function"""
    print("🎬 Advanced Flask Audio Transcription Test")
    print("=" * 50)

    # Verify server is running
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server returned unexpected status code:", response.status_code)
            return
    except requests.RequestException:
        print("❌ Server is not running on localhost:8000")
        print("Please start the Flask application first")
        return

    # List available test files from both directories
    test_dirs = [
        "/workspaces/codespaces-flask/audio files",
        "/workspaces/codespaces-flask/uploads"
    ]
    test_files = []
    
    print("\n📂 Scanning for test files...")
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            for file in os.listdir(test_dir):
                if file.endswith(('.mp3', '.mp4')) and not file.startswith('.'):
                    file_path = os.path.join(test_dir, file)
                    size = os.path.getsize(file_path)
                    test_files.append((file_path, size))
            print(f"  ✓ Scanned {test_dir}")

    if not test_files:
        print("❌ No test files found")
        return

    # Sort by file size and use smallest file
    test_files.sort(key=lambda x: x[1])
    smallest_file = test_files[0][0]

    print(f"\n📊 Found {len(test_files)} test files:")
    for file_path, size in test_files:
        name = os.path.basename(file_path)
        size_mb = size / (1024 * 1024)
        print(f"  • {name} ({size_mb:.2f} MB)")

    # Test multiple files, starting with the smallest
    print("\n🔄 Starting transcription tests...")
    test_files.sort(key=lambda x: x[1])  # Sort by file size
    test_count = min(3, len(test_files))  # Test up to 3 files
    
    results = []
    for i, (file_path, _) in enumerate(test_files[:test_count], 1):
        print(f"\n📊 Test {i}/{test_count}: {os.path.basename(file_path)}")
        print("-" * 50)
        success = test_upload(file_path)
        results.append((os.path.basename(file_path), success))
        time.sleep(1)  # Brief pause between tests
    
    # Print summary
    print("\n📋 Test Summary:")
    print("=" * 50)
    successful = sum(1 for _, success in results if success)
    print(f"✓ {successful}/{len(results)} tests passed")
    
    for filename, success in results:
        status = "✅ Passed" if success else "❌ Failed"
        print(f"{status} - {filename}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check Flask server logs for errors")
        print("2. Verify all dependencies are installed")
        print("3. Ensure enough system resources are available")
        print("4. Check audio file format is supported")

if __name__ == "__main__":
    main()
