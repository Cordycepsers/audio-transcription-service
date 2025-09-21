#!/usr/bin/env python3
"""
Alert Webhook Script for Audio Transcription Service
Sends alerts to Slack, Discord, or other webhook endpoints when issues are detected
"""

import requests
import json
import sys
import os
from datetime import datetime
from health_check import check_health

class AlertManager:
    def __init__(self):
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        self.custom_webhook = os.getenv('CUSTOM_WEBHOOK_URL')
        
    def send_slack_alert(self, message, color="danger"):
        """Send alert to Slack"""
        if not self.slack_webhook:
            return False
            
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": "🚨 Audio Transcription Service Alert",
                    "text": message,
                    "footer": "Heroku Monitoring",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        try:
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
            return False
    
    def send_discord_alert(self, message):
        """Send alert to Discord"""
        if not self.discord_webhook:
            return False
            
        payload = {
            "embeds": [
                {
                    "title": "🚨 Audio Transcription Service Alert",
                    "description": message,
                    "color": 15158332,  # Red color
                    "timestamp": datetime.now().isoformat(),
                    "footer": {
                        "text": "Heroku Monitoring"
                    }
                }
            ]
        }
        
        try:
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            return response.status_code == 204
        except Exception as e:
            print(f"Failed to send Discord alert: {e}")
            return False
    
    def send_custom_alert(self, health_results):
        """Send alert to custom webhook"""
        if not self.custom_webhook:
            return False
            
        payload = {
            "service": "audio-transcription-service",
            "alert_type": "health_check_failure",
            "timestamp": datetime.now().isoformat(),
            "health_results": health_results
        }
        
        try:
            response = requests.post(self.custom_webhook, json=payload, timeout=10)
            return response.status_code in [200, 201, 202]
        except Exception as e:
            print(f"Failed to send custom alert: {e}")
            return False
    
    def format_alert_message(self, health_results):
        """Format health check results into alert message"""
        failed_checks = []
        for check_name, result in health_results['checks'].items():
            if result['status'] == 'fail':
                error_msg = result.get('error', 'Unknown error')
                failed_checks.append(f"• {check_name.replace('_', ' ').title()}: {error_msg}")
        
        if not failed_checks:
            return "Service is healthy ✅"
        
        message = f"""**Service Health Check Failed**
        
**URL:** {health_results['base_url']}
**Time:** {health_results['timestamp']}
**Overall Status:** {health_results['overall_status'].upper()}

**Failed Checks:**
{chr(10).join(failed_checks)}

**Action Required:** Please investigate the service immediately."""
        
        return message
    
    def send_alerts(self, health_results):
        """Send alerts to all configured channels"""
        if health_results['overall_status'] == 'healthy':
            return True
        
        message = self.format_alert_message(health_results)
        results = []
        
        # Send to Slack
        if self.slack_webhook:
            slack_result = self.send_slack_alert(message)
            results.append(('Slack', slack_result))
            print(f"Slack alert: {'✅ Sent' if slack_result else '❌ Failed'}")
        
        # Send to Discord
        if self.discord_webhook:
            discord_result = self.send_discord_alert(message)
            results.append(('Discord', discord_result))
            print(f"Discord alert: {'✅ Sent' if discord_result else '❌ Failed'}")
        
        # Send to custom webhook
        if self.custom_webhook:
            custom_result = self.send_custom_alert(health_results)
            results.append(('Custom', custom_result))
            print(f"Custom webhook alert: {'✅ Sent' if custom_result else '❌ Failed'}")
        
        return any(result[1] for result in results)

def main():
    if len(sys.argv) != 2:
        print("Usage: python alert_webhook.py <base_url>")
        print("Example: python alert_webhook.py https://your-app.herokuapp.com")
        print()
        print("Environment variables:")
        print("  SLACK_WEBHOOK_URL - Slack webhook URL for alerts")
        print("  DISCORD_WEBHOOK_URL - Discord webhook URL for alerts")
        print("  CUSTOM_WEBHOOK_URL - Custom webhook URL for alerts")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print(f"🔍 Checking health and sending alerts for: {base_url}")
    print("=" * 60)
    
    # Run health check
    health_results = check_health(base_url)
    
    # Initialize alert manager
    alert_manager = AlertManager()
    
    # Print health status
    status_emoji = "✅" if health_results['overall_status'] == 'healthy' else "❌"
    print(f"{status_emoji} Service Status: {health_results['overall_status'].upper()}")
    
    # Send alerts if unhealthy
    if health_results['overall_status'] != 'healthy':
        print("\n🚨 Service is unhealthy - sending alerts...")
        alert_sent = alert_manager.send_alerts(health_results)
        
        if alert_sent:
            print("✅ Alerts sent successfully")
        else:
            print("❌ Failed to send alerts (check webhook configuration)")
            
        # Exit with error code for monitoring systems
        sys.exit(1)
    else:
        print("✅ Service is healthy - no alerts needed")
        sys.exit(0)

if __name__ == "__main__":
    main()