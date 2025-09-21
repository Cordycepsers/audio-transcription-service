

### 1. Install Production Dependencies

```bash
pip install gunicorn
```

### 2. Create Production Configuration

Create `gunicorn.conf.py`:
```python
bind = "0.0.0.0:8080"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 300  # 5 minutes for long transcriptions
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
```

### 3. Production Startup Script

Create `start_production.sh`:
```bash
#!/bin/bash
export FLASK_ENV=production
gunicorn --config gunicorn.conf.py app:app
```

### 4. Environment Variables

Create `.env.production`:
```bash
# Whisper Configuration
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

# Google Sheets (fix credentials first)
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_WORKSHEET_NAME=your_worksheet_name

# Flask
FLASK_ENV=production
SECRET_KEY=your_secret_key_here
```

## 🔧 Fixing Google Sheets Integration

### Issue: "Invalid JWT Signature"

**Root Cause**: Service account credentials are not properly configured.

**Solutions**:

1. **Regenerate Service Account Key**:
   ```bash
   # In Google Cloud Console:
   # 1. Go to IAM & Admin > Service Accounts
   # 2. Find your service account
   # 3. Create new key (JSON format)
   # 4. Replace service-account.json
   ```

2. **Verify API Access**:
   ```bash
   # Ensure these APIs are enabled:
   # - Google Sheets API
   # - Google Drive API
   ```

3. **Test Credentials**:
   ```python
   import gspread
   from google.oauth2.service_account import Credentials
   
   # Test script
   gc = gspread.service_account(filename='service-account.json')
   sheet = gc.open_by_key('your_sheet_id')
   print("✅ Google Sheets connection successful!")
   ```

## 🐳 Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads transcripts

# Expose port
EXPOSE 8080

# Start command
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```

Build and run:
```bash
docker build -t transcript-service .
docker run -p 8080:8080 -v $(pwd)/transcripts:/app/transcripts transcript-service
```

## ☁️ Cloud Deployment Options

### 1. Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/transcript-service
gcloud run deploy --image gcr.io/PROJECT_ID/transcript-service --platform managed
```

### 2. AWS ECS/Fargate
```bash
# Push to ECR and deploy with ECS
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin
docker tag transcript-service:latest AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/transcript-service:latest
docker push AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/transcript-service:latest
```

### 3. Heroku
```bash
# Create Procfile
echo "web: gunicorn --config gunicorn.conf.py app:app" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

## 📊 Performance Optimization

### 1. Whisper Model Selection
```python
# For better performance vs accuracy trade-off:
WHISPER_MODEL = "base"      # Fast, good quality
WHISPER_MODEL = "small"     # Balanced
WHISPER_MODEL = "medium"    # Better quality, slower
WHISPER_MODEL = "large"     # Best quality, slowest
```

### 2. Hardware Recommendations
- **CPU**: 4+ cores for concurrent transcriptions
- **RAM**: 8GB+ (Whisper models are memory intensive)
- **Storage**: SSD for faster file I/O
- **GPU**: Optional, for faster transcription with CUDA

### 3. Scaling Considerations
- Use Redis for session storage in multi-instance deployments
- Implement file upload size limits
- Add rate limiting for API endpoints
- Use CDN for static assets

## 🔒 Security Checklist

- [ ] Change default secret keys
- [ ] Enable HTTPS in production
- [ ] Implement file upload validation
- [ ] Add authentication if needed
- [ ] Secure Google service account credentials
- [ ] Set up proper CORS policies
- [ ] Implement request rate limiting
- [ ] Regular security updates

## 📈 Monitoring

### Health Check Endpoint
The app includes `/health` endpoint for monitoring:
```bash
curl http://localhost:8080/health
# Response: {"status": "healthy", "timestamp": "..."}
```

### Logging
- Application logs are written to stdout
- Configure log aggregation (ELK stack, CloudWatch, etc.)
- Monitor transcription success/failure rates

## 🎯 Next Steps

1. **Fix Google Sheets credentials** for full functionality
2. **Choose deployment platform** based on your needs
3. **Set up monitoring and alerting**
4. **Implement authentication** if required
5. **Add file size limits** and validation
6. **Set up automated backups** for transcripts

## 📞 Support

For issues or questions:
- Check server logs for detailed error messages
- Verify all dependencies are installed
- Test with small audio files first
- Ensure sufficient disk space for uploads

---

**Status**: ✅ Ready for production deployment (pending Google Sheets fix)