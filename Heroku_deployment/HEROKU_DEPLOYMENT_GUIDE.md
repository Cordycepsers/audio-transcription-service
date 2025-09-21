# 🚀 Heroku Deployment Guide - Audio Transcription Service

## 📋 Prerequisites

1. **Heroku Account**: Sign up at [heroku.com](https://heroku.com)
2. **Heroku CLI**: Install from [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
3. **Git**: Ensure git is installed and configured
4. **Google Service Account**: JSON key file ready

## 🔧 Step 1: Prepare for Deployment

### 1.1 Login to Heroku
```bash
heroku login
```

### 1.2 Create Heroku App
```bash
# Replace 'your-app-name' with your desired app name
heroku create your-transcription-app

# Or let Heroku generate a name
heroku create
```

### 1.3 Add Required Buildpacks
```bash
# Add FFmpeg buildpack (required for audio processing)
heroku buildpacks:add --index 1 https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git

# Add Python buildpack
heroku buildpacks:add --index 2 heroku/python
```

## 🔐 Step 2: Configure Environment Variables

### 2.1 Set Required Environment Variables
```bash
# Flask environment
heroku config:set FLASK_ENV=production

# Google Sheets configuration
heroku config:set GOOGLE_SHEET_ID="your-google-sheet-id"
heroku config:set GOOGLE_WORKSHEET_NAME="TRANSCRIPT FINAL"
heroku config:set SERVICE_ACCOUNT_EMAIL="your-service-account@project.iam.gserviceaccount.com"

# File upload limit (100MB)
heroku config:set MAX_CONTENT_LENGTH=104857600

# Optional: Sentry for error monitoring
heroku config:set SENTRY_DSN="your-sentry-dsn-url"
```

### 2.2 Upload Google Service Account Key
```bash
# Method 1: Base64 encode the service account JSON
cat service-account.json | base64 | tr -d '\n' > service-account-base64.txt
heroku config:set GOOGLE_SERVICE_ACCOUNT_KEY="$(cat service-account-base64.txt)"

# Method 2: Use Heroku's config vars (for smaller files)
heroku config:set GOOGLE_SERVICE_ACCOUNT_JSON="$(cat service-account.json)"
```

## 📦 Step 3: Add Monitoring Add-ons

### 3.1 Add Papertrail for Logging
```bash
heroku addons:create papertrail:choklad
```

### 3.2 Add New Relic for Performance Monitoring (Optional)
```bash
heroku addons:create newrelic:wayne
```

### 3.3 Add Heroku Scheduler for Health Checks (Optional)
```bash
heroku addons:create scheduler:standard
```

## 🚀 Step 4: Deploy to Heroku

### 4.1 Initialize Git Repository (if not already done)
```bash
git init
git add .
git commit -m "Initial commit for Heroku deployment"
```

### 4.2 Add Heroku Remote
```bash
heroku git:remote -a your-transcription-app
```

### 4.3 Deploy
```bash
git push heroku main
```

### 4.4 Scale the Application
```bash
# Start with 1 web dyno
heroku ps:scale web=1
```

## 🔍 Step 5: Verify Deployment

### 5.1 Check Application Status
```bash
heroku ps
heroku logs --tail
```

### 5.2 Test Health Endpoints
```bash
# Get your app URL
heroku info

# Test health check
curl https://your-app.herokuapp.com/health

# Test web interface
curl https://your-app.herokuapp.com/
```

### 5.3 Run Health Check Script
```bash
python monitoring/health_check.py https://your-app.herokuapp.com
```

## 📊 Step 6: Set Up Monitoring & Alerting

### 6.1 Configure Webhook Alerts

#### Slack Integration
1. Create a Slack webhook: [api.slack.com/messaging/webhooks](https://api.slack.com/messaging/webhooks)
2. Set the webhook URL:
```bash
heroku config:set SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

#### Discord Integration
1. Create a Discord webhook in your server settings
2. Set the webhook URL:
```bash
heroku config:set DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK"
```

### 6.2 Set Up External Monitoring

#### UptimeRobot (Free)
1. Sign up at [uptimerobot.com](https://uptimerobot.com)
2. Create HTTP(s) monitor for: `https://your-app.herokuapp.com/health`
3. Set check interval to 5 minutes
4. Configure alert contacts (email, SMS, webhook)

#### Pingdom
1. Sign up at [pingdom.com](https://pingdom.com)
2. Create uptime check for your app URL
3. Set up alert integrations

### 6.3 Configure Heroku Scheduler for Automated Health Checks
```bash
# Open scheduler dashboard
heroku addons:open scheduler

# Add job: python monitoring/alert_webhook.py https://your-app.herokuapp.com
# Schedule: Every 10 minutes
```

## 🔧 Step 7: Production Optimizations

### 7.1 Configure Dyno Settings
```bash
# Use Basic or Standard dynos for better performance
heroku ps:type web=basic

# Or for higher traffic
heroku ps:type web=standard-1x
```

### 7.2 Set Up Custom Domain (Optional)
```bash
heroku domains:add your-domain.com
heroku certs:auto:enable
```

### 7.3 Configure Database (if needed in future)
```bash
heroku addons:create heroku-postgresql:mini
```

## 🚨 Step 8: Monitoring Dashboard Setup

### 8.1 Heroku Metrics
- Access via Heroku Dashboard → Your App → Metrics
- Monitor response times, throughput, memory usage

### 8.2 Papertrail Logs
```bash
heroku addons:open papertrail
```

### 8.3 Custom Monitoring Endpoints
- Health: `https://your-app.herokuapp.com/health`
- Status: `https://your-app.herokuapp.com/status`
- Metrics: `https://your-app.herokuapp.com/metrics`

## 🔄 Step 9: Continuous Deployment

### 9.1 GitHub Integration
1. Connect your Heroku app to GitHub repository
2. Enable automatic deploys from main branch
3. Enable "Wait for CI to pass before deploy"

### 9.2 Review Apps (Optional)
```bash
# Enable review apps for pull requests
heroku features:enable review-apps
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Build Failures
```bash
# Check build logs
heroku logs --tail --dyno=build

# Common fixes:
# - Ensure requirements.txt is up to date
# - Check Python version in runtime.txt
# - Verify buildpack order
```

#### 2. Application Crashes
```bash
# Check application logs
heroku logs --tail

# Restart application
heroku restart

# Check dyno status
heroku ps
```

#### 3. Memory Issues
```bash
# Monitor memory usage
heroku logs --tail | grep "Memory"

# Scale to larger dyno
heroku ps:type web=standard-1x
```

#### 4. Timeout Issues
```bash
# Increase timeout in Procfile
# web: gunicorn --bind 0.0.0.0:$PORT --timeout 300 app:app
```

### Debug Commands
```bash
# Run one-off dyno for debugging
heroku run bash

# Check environment variables
heroku config

# View recent releases
heroku releases

# Rollback to previous release
heroku rollback v123
```

## 📈 Performance Optimization

### 1. Gunicorn Configuration
The `Procfile` is optimized for Heroku:
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 --worker-class sync --max-requests 1000 --preload app:app
```

### 2. Memory Management
- Use `--preload` to reduce memory usage
- Limit workers based on dyno memory
- Monitor memory usage via Heroku metrics

### 3. Caching
- Consider adding Redis for caching (future enhancement)
- Use CDN for static assets if needed

## 🔒 Security Checklist

- ✅ Environment variables for sensitive data
- ✅ HTTPS enforced by Heroku
- ✅ Service account with minimal permissions
- ✅ File upload validation
- ✅ Error monitoring with Sentry
- ✅ Regular security updates

## 📞 Support & Maintenance

### Regular Tasks
1. **Monitor logs daily** via Papertrail
2. **Check health endpoints** weekly
3. **Update dependencies** monthly
4. **Review metrics** for performance trends
5. **Test backup/restore** procedures

### Emergency Procedures
1. **Scale down**: `heroku ps:scale web=0`
2. **Scale up**: `heroku ps:scale web=1`
3. **Restart**: `heroku restart`
4. **Rollback**: `heroku rollback`

---

## 🎉 Deployment Complete!

Your Audio Transcription Service is now deployed on Heroku with:

- ✅ **Production-ready configuration**
- ✅ **Comprehensive monitoring**
- ✅ **Automated alerting**
- ✅ **Health checks**
- ✅ **Error tracking**
- ✅ **Performance monitoring**

### Quick Access URLs
- **Application**: `https://your-app.herokuapp.com`
- **Health Check**: `https://your-app.herokuapp.com/health`
- **Status**: `https://your-app.herokuapp.com/status`
- **Metrics**: `https://your-app.herokuapp.com/metrics`

### Next Steps
1. Set up external monitoring (UptimeRobot/Pingdom)
2. Configure alert webhooks (Slack/Discord)
3. Test the complete workflow
4. Share the URL with your team!

**🚀 Your transcription service is live and ready for production use! 🚀**