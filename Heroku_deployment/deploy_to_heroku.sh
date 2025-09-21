#!/bin/bash

# Heroku Deployment Script for wtysl app
# Usage: ./deploy_to_heroku.sh [HEROKU_API_KEY]

set -e

APP_NAME="wtysl"
CURRENT_BRANCH=$(git branch --show-current)

echo "🚀 Starting Heroku deployment for app: $APP_NAME"
echo "📍 Current branch: $CURRENT_BRANCH"

# Check if Heroku API key is provided
if [ -n "$1" ]; then
    export HEROKU_API_KEY="$1"
    echo "✅ Using provided API key"
elif [ -n "$HEROKU_API_KEY" ]; then
    echo "✅ Using environment variable API key"
else
    echo "❌ Error: Heroku API key required"
    echo "Usage: ./deploy_to_heroku.sh [HEROKU_API_KEY]"
    echo "Or set HEROKU_API_KEY environment variable"
    exit 1
fi

# Authenticate with Heroku using API key
echo "🔐 Authenticating with Heroku..."
echo "$HEROKU_API_KEY" | heroku auth:token

# Check if app exists, create if it doesn't
echo "🔍 Checking if app '$APP_NAME' exists..."
if heroku apps:info $APP_NAME >/dev/null 2>&1; then
    echo "✅ App '$APP_NAME' already exists"
else
    echo "📦 Creating new Heroku app: $APP_NAME"
    heroku create $APP_NAME
fi

# Add buildpacks
echo "🔧 Setting up buildpacks..."
heroku buildpacks:clear -a $APP_NAME
heroku buildpacks:add --index 1 https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git -a $APP_NAME
heroku buildpacks:add --index 2 heroku/python -a $APP_NAME

# Add Heroku remote if it doesn't exist
echo "🔗 Setting up git remote..."
if git remote get-url heroku >/dev/null 2>&1; then
    echo "✅ Heroku remote already exists"
else
    heroku git:remote -a $APP_NAME
fi

# Set basic environment variables
echo "⚙️ Setting environment variables..."
heroku config:set FLASK_ENV=production -a $APP_NAME
heroku config:set MAX_CONTENT_LENGTH=104857600 -a $APP_NAME
heroku config:set GOOGLE_WORKSHEET_NAME="TRANSCRIPT FINAL" -a $APP_NAME

# Add Papertrail addon for logging
echo "📊 Adding Papertrail addon..."
if heroku addons:info papertrail -a $APP_NAME >/dev/null 2>&1; then
    echo "✅ Papertrail addon already exists"
else
    heroku addons:create papertrail:choklad -a $APP_NAME
fi

# Deploy to Heroku
echo "🚀 Deploying to Heroku..."
git push heroku $CURRENT_BRANCH:main

# Scale the application
echo "📈 Scaling application..."
heroku ps:scale web=1 -a $APP_NAME

# Show deployment info
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📱 App URL: https://$APP_NAME.herokuapp.com"
echo "🔍 Health Check: https://$APP_NAME.herokuapp.com/health"
echo "📊 Status: https://$APP_NAME.herokuapp.com/status"
echo ""
echo "📋 Next steps:"
echo "1. Set required environment variables:"
echo "   heroku config:set GOOGLE_SHEET_ID='your-sheet-id' -a $APP_NAME"
echo "   heroku config:set SERVICE_ACCOUNT_EMAIL='your-service-account@project.iam.gserviceaccount.com' -a $APP_NAME"
echo "   heroku config:set GOOGLE_SERVICE_ACCOUNT_JSON='$(cat service-account.json)' -a $APP_NAME"
echo ""
echo "2. Optional: Set Sentry DSN for error monitoring:"
echo "   heroku config:set SENTRY_DSN='your-sentry-dsn' -a $APP_NAME"
echo ""
echo "3. Check logs:"
echo "   heroku logs --tail -a $APP_NAME"
echo ""
echo "4. Test the application:"
echo "   curl https://$APP_NAME.herokuapp.com/health"
echo ""

# Show current config
echo "🔧 Current configuration:"
heroku config -a $APP_NAME

echo ""
echo "✅ Deployment script completed!"