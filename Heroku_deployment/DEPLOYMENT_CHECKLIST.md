# 🚀 Heroku Deployment Checklist - Audio Transcription Service

## ✅ Pre-Deployment Checklist

### 📋 Required Files
- [ ] `Procfile` - Gunicorn configuration for Heroku
- [ ] `runtime.txt` - Python version specification
- [ ] `requirements.txt` - All dependencies listed
- [ ] `app.json` - Heroku app configuration
- [ ] `heroku.yml` - Alternative deployment configuration
- [ ] `.slugignore` - Files to exclude from deployment
- [ ] `service-account.json` - Google Service Account key

### 🔧 Code Preparation
- [ ] Environment variable handling for Heroku (`PORT`, `GOOGLE_SERVICE_ACCOUNT_KEY`)
- [ ] Base64 service account key decoding implemented
- [ ] Sentry error monitoring integrated
- [ ] Health check endpoints added (`/health`, `/status`, `/metrics`)
- [ ] Production logging configuration
- [ ] Debug mode disabled for production

### 🔐 Environment Variables
- [ ] `FLASK_ENV=production`
- [ ] `GOOGLE_SHEET_ID` - Your Google Sheet ID
- [ ] `GOOGLE_WORKSHEET_NAME` - Worksheet name (default: "TRANSCRIPT FINAL")
- [ ] `SERVICE_ACCOUNT_EMAIL` - Google Service Account email
- [ ] `GOOGLE_SERVICE_ACCOUNT_KEY` - Base64 encoded service account JSON
- [ ] `MAX_CONTENT_LENGTH=104857600` - File upload limit (100MB)
- [ ] `SENTRY_DSN` - Error monitoring (optional)

## 🚀 Deployment Steps

### 1. Heroku Setup
- [ ] Heroku CLI installed and logged in
- [ ] Heroku app created: `heroku create your-app-name`
- [ ] Buildpacks added:
  - [ ] FFmpeg: `heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git`
  - [ ] Python: `heroku buildpacks:add heroku/python`

### 2. Environment Configuration
- [ ] Run setup script: `python setup_heroku_env.py`
- [ ] Or manually set variables: `heroku config:set VAR_NAME=value`
- [ ] Verify configuration: `heroku config`

### 3. Add-ons Installation
- [ ] Papertrail logging: `heroku addons:create papertrail:choklad`
- [ ] New Relic monitoring (optional): `heroku addons:create newrelic:wayne`
- [ ] Heroku Scheduler (optional): `heroku addons:create scheduler:standard`

### 4. Deployment
- [ ] Git repository initialized
- [ ] All files committed: `git add . && git commit -m "Deploy to Heroku"`
- [ ] Heroku remote added: `heroku git:remote -a your-app-name`
- [ ] Deploy: `git push heroku main`
- [ ] Scale application: `heroku ps:scale web=1`

## 🔍 Post-Deployment Verification

### 1. Basic Health Checks
- [ ] App status: `heroku ps`
- [ ] Logs check: `heroku logs --tail`
- [ ] Health endpoint: `curl https://your-app.herokuapp.com/health`
- [ ] Web interface: Visit `https://your-app.herokuapp.com`

### 2. Comprehensive Testing
- [ ] Run deployment test: `python test_deployment.py https://your-app.herokuapp.com`
- [ ] Test file upload via web interface
- [ ] Verify Google Sheets integration
- [ ] Check all monitoring endpoints

### 3. Performance Verification
- [ ] Response times under 30 seconds for health checks
- [ ] Memory usage within dyno limits
- [ ] No immediate crashes or restarts

## 📊 Monitoring Setup

### 1. Built-in Monitoring
- [ ] Heroku Metrics dashboard configured
- [ ] Papertrail logs accessible
- [ ] Application performance baseline established

### 2. External Monitoring
- [ ] UptimeRobot monitor created for `/health` endpoint
- [ ] Pingdom uptime check configured (optional)
- [ ] Custom monitoring dashboard setup (optional)

### 3. Alerting Configuration
- [ ] Slack webhook configured: `heroku config:set SLACK_WEBHOOK_URL=...`
- [ ] Discord webhook configured: `heroku config:set DISCORD_WEBHOOK_URL=...`
- [ ] Alert script tested: `python monitoring/alert_webhook.py https://your-app.herokuapp.com`

### 4. Automated Health Checks
- [ ] Heroku Scheduler job added for health monitoring
- [ ] Schedule: Every 10 minutes
- [ ] Command: `python monitoring/alert_webhook.py https://your-app.herokuapp.com`

## 🔒 Security Checklist

### 1. Environment Security
- [ ] No sensitive data in code repository
- [ ] Service account key properly encoded and stored
- [ ] Environment variables properly configured
- [ ] Debug mode disabled in production

### 2. Application Security
- [ ] File upload validation enabled
- [ ] File size limits configured
- [ ] Temporary file cleanup working
- [ ] Error messages don't leak sensitive information

### 3. Access Control
- [ ] Google Service Account has minimal required permissions
- [ ] Google Sheets properly shared with service account
- [ ] No unnecessary API keys or credentials

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

#### 1. Build Failures
**Problem**: Deployment fails during build
**Solutions**:
- [ ] Check `heroku logs --tail --dyno=build`
- [ ] Verify `requirements.txt` is complete
- [ ] Ensure `runtime.txt` specifies correct Python version
- [ ] Check buildpack order

#### 2. Application Crashes
**Problem**: App starts but crashes immediately
**Solutions**:
- [ ] Check `heroku logs --tail`
- [ ] Verify environment variables: `heroku config`
- [ ] Test service account key decoding
- [ ] Check for missing dependencies

#### 3. Service Account Issues
**Problem**: Google Sheets integration fails
**Solutions**:
- [ ] Verify `GOOGLE_SERVICE_ACCOUNT_KEY` is properly base64 encoded
- [ ] Check service account email in environment variables
- [ ] Ensure Google Sheet is shared with service account
- [ ] Test service account permissions

#### 4. Memory Issues
**Problem**: App exceeds memory limits
**Solutions**:
- [ ] Upgrade to larger dyno: `heroku ps:type web=standard-1x`
- [ ] Monitor memory usage via Heroku Metrics
- [ ] Optimize Whisper model usage
- [ ] Implement file size limits

#### 5. Timeout Issues
**Problem**: Requests timeout
**Solutions**:
- [ ] Increase timeout in `Procfile`
- [ ] Optimize transcription performance
- [ ] Consider async processing for large files
- [ ] Monitor response times

## 📈 Performance Optimization

### 1. Dyno Configuration
- [ ] Start with Basic dyno for testing
- [ ] Monitor performance metrics
- [ ] Scale to Standard-1X if needed
- [ ] Consider multiple dynos for high traffic

### 2. Application Optimization
- [ ] Whisper model preloading (optional)
- [ ] File processing optimization
- [ ] Memory usage monitoring
- [ ] Response time optimization

### 3. Monitoring and Alerting
- [ ] Set up performance baselines
- [ ] Configure alerting thresholds
- [ ] Regular performance reviews
- [ ] Capacity planning

## 🎯 Success Criteria

### ✅ Deployment Successful When:
- [ ] All health endpoints return 200 OK
- [ ] Web interface loads and functions correctly
- [ ] File upload and transcription works end-to-end
- [ ] Google Sheets integration saves transcripts
- [ ] Monitoring and alerting is functional
- [ ] Performance meets requirements (< 30s response times)
- [ ] No critical errors in logs
- [ ] External monitoring confirms uptime

### 📊 Key Metrics to Monitor:
- **Uptime**: > 99.5%
- **Response Time**: < 30 seconds for health checks
- **Error Rate**: < 1%
- **Memory Usage**: < 80% of dyno limit
- **Transcription Success Rate**: > 95%

## 🎉 Post-Deployment Tasks

### 1. Documentation
- [ ] Update README with production URL
- [ ] Document monitoring procedures
- [ ] Create user guide for the service
- [ ] Document troubleshooting procedures

### 2. Team Communication
- [ ] Share production URL with team
- [ ] Provide access to monitoring dashboards
- [ ] Set up on-call procedures
- [ ] Schedule regular health checks

### 3. Maintenance Planning
- [ ] Schedule regular dependency updates
- [ ] Plan for scaling requirements
- [ ] Set up backup procedures
- [ ] Create disaster recovery plan

---

## 🏆 Deployment Complete!

**Congratulations! Your Audio Transcription Service is now live on Heroku with comprehensive monitoring and alerting.**

### Quick Access Links:
- **Application**: `https://your-app.herokuapp.com`
- **Health Check**: `https://your-app.herokuapp.com/health`
- **Status Dashboard**: `https://your-app.herokuapp.com/status`
- **Metrics**: `https://your-app.herokuapp.com/metrics`
- **Heroku Dashboard**: `https://dashboard.heroku.com/apps/your-app-name`
- **Papertrail Logs**: `heroku addons:open papertrail`

### Emergency Contacts:
- **Scale Down**: `heroku ps:scale web=0`
- **Scale Up**: `heroku ps:scale web=1`
- **Restart**: `heroku restart`
- **Logs**: `heroku logs --tail`
- **Rollback**: `heroku rollback`

**🚀 Your service is production-ready and monitored! 🚀**