#!/bin/bash
# Deployment script for Flask VideoAsk Webhook Application

# Exit on error
set -e

echo "===== Flask VideoAsk Webhook Deployment Script ====="

# 1. Set project ID - replace with your actual project ID
PROJECT_ID="starry-computer-457800-b8"
echo "Setting project ID to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# 2. Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com \
  sheets.googleapis.com

# 3. Create service account key secret (if not already created)
echo "Creating secret for service account key..."
if ! gcloud secrets describe service-account-key > /dev/null 2>&1; then
  gcloud secrets create service-account-key --data-file=service-account.json
  echo "Secret created successfully"
else
  echo "Secret already exists, updating..."
  gcloud secrets versions add service-account-key --data-file=service-account.json
fi

# 4. Build and push the Docker image
echo "Building and pushing Docker image..."
IMAGE="gcr.io/${PROJECT_ID}/flask-videoask-webhook:latest"
docker build -t $IMAGE .
docker push $IMAGE

# 5. Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy flask-videoask-webhook \
  --image=$IMAGE \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --set-env-vars="GOOGLE_SHEET_ID=1s6OxhfqfQfxHH4M4ln1C1hrN3DWM8HI_-QJlY_p-KRU,GSHEET_WORKSHEET_NAME=TRANSCRIPT FINAL,VIDEOASK_GOOGLE_SHEET_ID=1s6OxhfqfQfxHH4M4ln1C1hrN3DWM8HI_-QJlY_p-KRU,VIDEOASK_GSHEET_WORKSHEET_NAME=TRANSCRIPT FINAL"

# 6. Mount the service account secret
echo "Mounting service account secret..."
gcloud run services update flask-videoask-webhook \
  --region=us-central1 \
  --add-volume=name=service-account,type=secret,secret=service-account-key,target-path=/app/service-account.json

# 7. Get the deployment URL
SERVICE_URL=$(gcloud run services describe flask-videoask-webhook --region=us-central1 --format='value(status.url)')
echo ""
echo "=== Deployment Complete! ==="
echo "Your service is deployed at: $SERVICE_URL"
echo ""
echo "Test your webhook with:"
echo "curl -X POST ${SERVICE_URL}/webhook/videoask \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"event_type\": \"form_response\", \"contact\": {\"email\": \"test@example.com\"}}'"
