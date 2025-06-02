# Google Cloud Deployment Guide

This guide details how to deploy the Flask application with VideoAsk webhook integration to Google Cloud Run.

## Prerequisites

1. [Google Cloud account](https://console.cloud.google.com/)
2. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
3. [Docker](https://docs.docker.com/get-docker/) installed (for local testing)

## Step 1: Set Up Google Cloud Project

```bash
# Set project ID
export PROJECT_ID="starry-computer-457800-b8"

# Configure gcloud with your project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com \
  sheets.googleapis.com
```

## Step 2: Set Up Service Account for Google Sheets

1. Make sure you've shared your Google Sheet with the service account:
   `1053893186121-compute@developer.gserviceaccount.com`

2. Ensure Google Sheets API is enabled in your project.

3. Store the service account key (already saved as `service-account.json`).

## Step 3: Build and Deploy with Cloud Build

```bash
# Upload service account to Secret Manager
gcloud secrets create service-account-key --data-file=service-account.json

# Deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml
```

## Step 4: Set Up Environment Variables in Cloud Run

If you need to update environment variables:

```bash
gcloud run services update flask-videoask-webhook \
  --set-env-vars="GOOGLE_SHEET_ID=1s6OxhfqfQfxHH4M4ln1C1hrN3DWM8HI_-QJlY_p-KRU,GSHEET_WORKSHEET_NAME=TRANSCRIPT FINAL"
```

## Step 5: Mount Service Account Secret

```bash
gcloud run services update flask-videoask-webhook \
  --add-volume=name=service-account,type=secret,secret=service-account-key,target-path=/app/service-account.json
```

## Step 6: Verify Deployment

1. Get the Cloud Run service URL:
   ```bash
   gcloud run services describe flask-videoask-webhook --format='value(status.url)'
   ```

2. Test the webhook endpoint:
   ```bash
   curl -X POST https://YOUR-SERVICE-URL/webhook/videoask \
     -H "Content-Type: application/json" \
     -d '{"event_type": "form_response", "contact": {"email": "test@example.com"}}'
   ```

## Troubleshooting

- **Logs**: View application logs in Google Cloud Console > Cloud Run > flask-videoask-webhook > Logs
- **Google Sheets Access**: Verify service account has editor access to the spreadsheet
- **API Enablement**: Ensure Google Sheets API is enabled

## Production Considerations

- Set up [Cloud Monitoring](https://cloud.google.com/monitoring) for alerts
- Configure [Cloud Logging](https://cloud.google.com/logging) for log analysis
- Set up [Cloud Scheduler](https://cloud.google.com/scheduler) for webhook testing
