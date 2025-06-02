#!/usr/bin/env python3
"""
Test script for VideoAsk webhook functionality.
This script tests all VideoAsk webhook endpoints and validates the integration.
"""

import requests
import json
import time
from datetime import datetime

# Base URL for the Flask application
BASE_URL = "http://localhost:8000"

def test_webhook_validation():
    """Test the webhook validation endpoint."""
    print("🔍 Testing webhook validation endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/webhook/validate")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Validation endpoint working")
            print(f"   Google Sheets Client: {'✅' if data.get('google_sheets_client') else '❌'}")
            print(f"   VideoAsk Sheet Access: {'✅' if data.get('videoask_sheet_access') else '❌'}")
            print(f"   Webhook Data Directory: {'✅' if data.get('webhook_data_directory') else '❌'}")
            
            env_vars = data.get('environment_variables', {})
            print("   Environment Variables:")
            for var, status in env_vars.items():
                print(f"     {var}: {'✅' if status else '❌'}")
            
            return True
        else:
            print(f"❌ Validation endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing validation endpoint: {e}")
        return False

def test_webhook_test_endpoint():
    """Test the webhook test endpoint."""
    print("\n🧪 Testing webhook test endpoint...")
    
    try:
        response = requests.post(f"{BASE_URL}/webhook/test", json={})
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Test endpoint working")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            
            mapped_data = data.get('mapped_data', {})
            print("   Mapped Data Sample:")
            for key, value in list(mapped_data.items())[:5]:
                print(f"     {key}: {value}")
            
            return True
        else:
            print(f"❌ Test endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing test endpoint: {e}")
        return False

def test_main_webhook_endpoint():
    """Test the main VideoAsk webhook endpoint."""
    print("\n🎯 Testing main VideoAsk webhook endpoint...")
    
    # Sample VideoAsk payload
    sample_payload = {
        "event_type": "form_response",
        "contact": {
            "name": "Test User",
            "email": f"test.user.{int(time.time())}@example.com",
            "created_at": datetime.now().isoformat() + "Z",
            "product_name": "Test Integration",
            "answers": [
                {
                    "question_id": "intro_q1",
                    "type": "video",
                    "transcription": "This is a test transcription from the integration test.",
                    "share_url": "https://example.com/share/test_intro"
                },
                {
                    "question_id": "influence_q1",
                    "type": "text",
                    "text": "Testing the influence question response.",
                    "share_url": "https://example.com/share/test_influence"
                },
                {
                    "question_id": "advice_q1",
                    "type": "video",
                    "transcription": "This is advice from our test user.",
                    "share_url": "https://example.com/share/test_advice"
                }
            ]
        },
        "form": {
            "questions": [
                {
                    "question_id": "intro_q1",
                    "label": "Introduce Yourself",
                    "title": "Tell us about yourself",
                    "share_url": "https://example.com/share/test_intro"
                },
                {
                    "question_id": "influence_q1",
                    "label": "Foundation's Influence",
                    "title": "How has the foundation influenced you?",
                    "share_url": "https://example.com/share/test_influence"
                },
                {
                    "question_id": "advice_q1",
                    "label": "Sharing Advice",
                    "title": "What advice would you share?",
                    "share_url": "https://example.com/share/test_advice"
                }
            ]
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/videoask",
            json=sample_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Main webhook endpoint working")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Main webhook endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing main webhook endpoint: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid payloads."""
    print("\n🚨 Testing error handling...")
    
    # Test with empty payload
    try:
        response = requests.post(f"{BASE_URL}/webhook/videoask", json={})
        if response.status_code == 400:
            print("✅ Empty payload handling working")
        else:
            print(f"⚠️  Unexpected response for empty payload: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing empty payload: {e}")
    
    # Test with no JSON
    try:
        response = requests.post(f"{BASE_URL}/webhook/videoask")
        if response.status_code == 400:
            print("✅ No JSON payload handling working")
        else:
            print(f"⚠️  Unexpected response for no JSON: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing no JSON: {e}")

def main():
    """Run all webhook tests."""
    print("🚀 Starting VideoAsk Webhook Integration Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/webhook/validate", timeout=5)
        print("✅ Flask server is running")
    except requests.exceptions.RequestException:
        print("❌ Flask server is not running. Please start the server first:")
        print("   python app.py")
        return
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if test_webhook_validation():
        tests_passed += 1
    
    if test_webhook_test_endpoint():
        tests_passed += 1
    
    if test_main_webhook_endpoint():
        tests_passed += 1
    
    test_error_handling()  # This doesn't contribute to pass/fail count
    
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All critical VideoAsk webhook functionality is working!")
        print("\n📋 Summary of Working Features:")
        print("   ✅ Webhook validation endpoint")
        print("   ✅ Test endpoint with sample data")
        print("   ✅ Main VideoAsk webhook processing")
        print("   ✅ Data mapping and local backup")
        print("   ✅ Error handling")
        
        print("\n🔗 Available Endpoints:")
        print(f"   POST {BASE_URL}/webhook/videoask - Main webhook endpoint")
        print(f"   POST {BASE_URL}/webhook/test - Test endpoint")
        print(f"   GET  {BASE_URL}/webhook/validate - Validation endpoint")
        
        print("\n⚠️  Note: Google Sheets integration may require valid service account credentials.")
    else:
        print("⚠️  Some tests failed. Please check the logs above.")

if __name__ == "__main__":
    main()
