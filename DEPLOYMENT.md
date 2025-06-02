# Production Deployment Guide for VideoAsk Webhook Integration

This guide covers deploying the Flask application with VideoAsk webhook integration to a production environment.

## Prerequisites

- Ubuntu/Linux server or cloud instance
- Domain name with SSL certificate
- Python 3.8+ installed
- Nginx or Apache web server
- Google Cloud service account with Sheets API access
- VideoAsk account with webhook capabilities

## Production Deployment Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install python3-pip python3-venv nginx supervisor ffmpeg git -y

# Create application user
sudo useradd -m -s /bin/bash videoask-app
sudo usermod -aG www-data videoask-app
```

### 2. Application Setup

```bash
# Switch to application user
sudo su - videoask-app

# Clone repository
git clone [your-repo-url] videoask-webhook-app
cd videoask-webhook-app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

### 3. Configuration

```bash
# Create production .env file
cp .env.example .env
nano .env
```

Configure your `.env` file:
```bash
# Google Sheets Configuration
GOOGLE_SHEET_ID="your-production-sheet-id"
GSHEET_WORKSHEET_NAME="TRANSCRIPT FINAL"
GOOGLE_SHEETS_CREDS_FILE="/home/videoask-app/videoask-webhook-app/service-account.json"

# VideoAsk Webhook Configuration  
VIDEOASK_GOOGLE_SHEET_ID="your-production-videoask-sheet-id"
VIDEOASK_GSHEET_WORKSHEET_NAME="VideoAsk Responses"

# Whisper Model Settings
WHISPER_MODEL="base.en"
COMPUTE_TYPE="int8"
DEVICE="cpu"

# Flask Configuration
FLASK_ENV="production"
FLASK_DEBUG="false"
```

### 4. Service Account Setup

```bash
# Upload your service account JSON file
# Ensure proper permissions
chmod 600 service-account.json
chown videoask-app:videoask-app service-account.json
```

### 5. Gunicorn Configuration

Create `/home/videoask-app/videoask-webhook-app/gunicorn.conf.py`:
```python
bind = "127.0.0.1:8000"
workers = 2
worker_class = "sync"
timeout = 300
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
user = "videoask-app"
group = "videoask-app"
```

### 6. Supervisor Configuration

Create `/etc/supervisor/conf.d/videoask-webhook.conf`:
```ini
[program:videoask-webhook]
command=/home/videoask-app/videoask-webhook-app/venv/bin/gunicorn -c gunicorn.conf.py app:app
directory=/home/videoask-app/videoask-webhook-app
user=videoask-app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/videoask-webhook.log
environment=PATH="/home/videoask-app/videoask-webhook-app/venv/bin"
```

### 7. Nginx Configuration

Create `/etc/nginx/sites-available/videoask-webhook`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /webhook/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 8. Start Services

```bash
# Enable and start supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor

# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Enable and restart nginx
sudo ln -s /etc/nginx/sites-available/videoask-webhook /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

# Start the application
sudo supervisorctl start videoask-webhook
```

### 9. Verify Deployment

```bash
# Check application status
sudo supervisorctl status videoask-webhook

# Check logs
sudo tail -f /var/log/videoask-webhook.log

# Test endpoints
curl https://your-domain.com/webhook/validate
curl -X POST https://your-domain.com/webhook/test
```

### 10. VideoAsk Webhook Configuration

1. Log into your VideoAsk account
2. Go to your form settings
3. Navigate to Integrations → Webhooks
4. Add webhook URL: `https://your-domain.com/webhook/videoask`
5. Select "Form Response" event
6. Test the webhook

## Monitoring and Maintenance

### Log Files
- Application logs: `/var/log/videoask-webhook.log`
- Nginx logs: `/var/log/nginx/access.log` and `/var/log/nginx/error.log`
- Webhook backups: `/home/videoask-app/videoask-webhook-app/webhook_data/`

### Health Checks
Set up monitoring for:
- `GET https://your-domain.com/webhook/validate` - Should return 200
- Disk space in webhook_data directory
- Google Sheets API quota usage

### Updates
```bash
# Pull latest changes
sudo su - videoask-app
cd videoask-webhook-app
git pull origin main

# Restart application
sudo supervisorctl restart videoask-webhook
```

## Security Considerations

1. **Firewall**: Only allow ports 80, 443, and SSH
2. **SSL**: Use strong SSL certificates (Let's Encrypt recommended)
3. **Secrets**: Store sensitive data in environment variables
4. **Backups**: Regular backups of webhook_data directory
5. **Updates**: Keep system and dependencies updated
6. **Monitoring**: Set up alerts for failed requests

## Troubleshooting

### Common Issues

**Application won't start:**
```bash
sudo supervisorctl tail videoask-webhook stderr
```

**Webhook responses fail:**
- Check Google Sheets API credentials
- Verify service account permissions
- Check network connectivity

**High memory usage:**
- Adjust Gunicorn worker count
- Monitor Whisper model loading

## Performance Optimization

1. **Gunicorn Workers**: Adjust based on CPU cores
2. **Caching**: Consider Redis for session management
3. **CDN**: Use CDN for static assets
4. **Database**: Consider PostgreSQL for larger data sets
5. **Queue**: Use Celery for background processing of large files

This deployment guide ensures a robust, scalable production environment for your VideoAsk webhook integration.
