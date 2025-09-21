#!/usr/bin/env python3
"""
Test suite for Flask audio transcription application
"""
import unittest
import tempfile
import os
import json
from app import app
import requests

class FlaskAppTestCase(unittest.TestCase):
    """Test cases for the Flask audio transcription app"""
    
    def setUp(self):
        """Set up test client"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
    
    def tearDown(self):
        """Clean up after tests"""
        self.ctx.pop()
    
    def test_home_page(self):
        """Test that the home page loads successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Audio Transcription App', response.data)
    
    def test_transcribe_endpoint_no_file(self):
        """Test transcribe endpoint with no file"""
        response = self.client.post('/transcribe')
        # Expecting 415 (Unsupported Media Type) when no multipart data is sent
        self.assertIn(response.status_code, [400, 415])
    
    def test_transcribe_endpoint_invalid_file(self):
        """Test transcribe endpoint with invalid file"""
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp:
            tmp.write(b'test content')
            tmp.seek(0)
            
            response = self.client.post('/transcribe', data={
                'audio': (tmp, 'test.txt')
            })
            # Expecting 400 or 415 for invalid file type
            self.assertIn(response.status_code, [400, 415])
    
    def test_health_check(self):
        """Test basic application health"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Check that the page contains expected elements
        self.assertIn(b'audio', response.data.lower())

class IntegrationTest(unittest.TestCase):
    """Integration tests for running application"""
    
    def test_server_running(self):
        """Test that the server is accessible"""
        try:
            response = requests.get('http://localhost:8000', timeout=5)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Audio Transcription App', response.text)
        except requests.exceptions.RequestException:
            self.skipTest("Server not running on localhost:8000")

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
