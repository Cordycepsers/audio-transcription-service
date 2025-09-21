#!/usr/bin/env python3
"""
Health Check Script for Audio Transcription Service
Can be used with external monitoring services like UptimeRobot, Pingdom, etc.
"""

import requests
import json
import sys
import time
from datetime import datetime

def check_health(base_url, timeout=30):
    """
    Comprehensive health check for the transcription service
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'base_url': base_url,
        'overall_status': 'healthy',
        'checks': {}
    }
    
    # Test 1: Basic health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=timeout)
        if response.status_code == 200:
            health_data = response.json()
            results['checks']['health_endpoint'] = {
                'status': 'pass',
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'data': health_data
            }
        else:
            results['checks']['health_endpoint'] = {
                'status': 'fail',
                'error': f"HTTP {response.status_code}",
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
            results['overall_status'] = 'unhealthy'
    except Exception as e:
        results['checks']['health_endpoint'] = {
            'status': 'fail',
            'error': str(e)
        }
        results['overall_status'] = 'unhealthy'
    
    # Test 2: Web interface
    try:
        response = requests.get(base_url, timeout=timeout)
        if response.status_code == 200 and 'Audio Transcription App' in response.text:
            results['checks']['web_interface'] = {
                'status': 'pass',
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
        else:
            results['checks']['web_interface'] = {
                'status': 'fail',
                'error': f"HTTP {response.status_code} or missing content"
            }
            results['overall_status'] = 'unhealthy'
    except Exception as e:
        results['checks']['web_interface'] = {
            'status': 'fail',
            'error': str(e)
        }
        results['overall_status'] = 'unhealthy'
    
    # Test 3: Status endpoint
    try:
        response = requests.get(f"{base_url}/status", timeout=timeout)
        if response.status_code == 200:
            status_data = response.json()
            results['checks']['status_endpoint'] = {
                'status': 'pass',
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'features': status_data.get('features', {})
            }
        else:
            results['checks']['status_endpoint'] = {
                'status': 'fail',
                'error': f"HTTP {response.status_code}"
            }
    except Exception as e:
        results['checks']['status_endpoint'] = {
            'status': 'fail',
            'error': str(e)
        }
    
    # Test 4: Metrics endpoint
    try:
        response = requests.get(f"{base_url}/metrics", timeout=timeout)
        if response.status_code == 200:
            results['checks']['metrics_endpoint'] = {
                'status': 'pass',
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
        else:
            results['checks']['metrics_endpoint'] = {
                'status': 'fail',
                'error': f"HTTP {response.status_code}"
            }
    except Exception as e:
        results['checks']['metrics_endpoint'] = {
            'status': 'fail',
            'error': str(e)
        }
    
    return results

def main():
    if len(sys.argv) != 2:
        print("Usage: python health_check.py <base_url>")
        print("Example: python health_check.py https://your-app.herokuapp.com")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print(f"🔍 Running health check for: {base_url}")
    print("=" * 50)
    
    results = check_health(base_url)
    
    # Print results
    print(f"⏰ Timestamp: {results['timestamp']}")
    print(f"🌐 Base URL: {results['base_url']}")
    print(f"📊 Overall Status: {results['overall_status'].upper()}")
    print()
    
    for check_name, check_result in results['checks'].items():
        status_emoji = "✅" if check_result['status'] == 'pass' else "❌"
        print(f"{status_emoji} {check_name.replace('_', ' ').title()}: {check_result['status'].upper()}")
        
        if 'response_time_ms' in check_result:
            print(f"   ⏱️  Response Time: {check_result['response_time_ms']:.2f}ms")
        
        if 'error' in check_result:
            print(f"   ⚠️  Error: {check_result['error']}")
        
        print()
    
    # Output JSON for programmatic use
    print("📋 JSON Output:")
    print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_status'] == 'healthy' else 1)

if __name__ == "__main__":
    main()