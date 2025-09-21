#!/bin/bash

# Security Remediation Script
# This script removes sensitive files from git tracking and secures the repository

echo "🔐 Security Remediation Script"
echo "=============================="
echo

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

echo "🔍 Current status of sensitive files:"
echo "- credentials.json: $(git ls-files | grep -q 'credentials.json' && echo 'TRACKED ❌' || echo 'not tracked ✅')"
echo "- .env: $(git ls-files | grep -q '^\.env$' && echo 'TRACKED ❌' || echo 'not tracked ✅')"
echo

# Prompt for confirmation
read -p "⚠️  Remove sensitive files from git tracking? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

echo "🚀 Starting remediation..."
echo

# Remove credentials.json from tracking if it exists
if git ls-files | grep -q 'credentials.json'; then
    echo "📝 Removing credentials.json from git tracking..."
    git rm --cached credentials.json
    echo "✅ credentials.json removed from tracking"
else
    echo "✅ credentials.json is not tracked"
fi

# Remove .env from tracking if it exists  
if git ls-files | grep -q '^\.env$'; then
    echo "📝 Removing .env from git tracking..."
    git rm --cached .env
    echo "✅ .env removed from tracking"
else
    echo "✅ .env is not tracked"
fi

echo
echo "📋 Updated .gitignore to include:"
echo "- credentials.json and other credential files"
echo "- .env* files (except .env.example)"
echo "- Additional security patterns"
echo

echo "🔄 Committing changes..."
git add .gitignore .env.example SECURITY_AUDIT_REPORT.md
git commit -m "Security: Remove sensitive files and improve .gitignore

- Remove credentials.json from tracking (contained OAuth client secret)  
- Remove .env from tracking (contained configuration data)
- Update .gitignore with comprehensive security patterns
- Add .env.example template for safe configuration
- Add security audit report with findings and recommendations

CRITICAL: OAuth client secret in credentials.json needs to be rotated!"

echo
echo "✅ Security remediation complete!"
echo
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "1. 🔑 Rotate the Google OAuth client secret immediately"
echo "2. 🔍 Review the SECURITY_AUDIT_REPORT.md for detailed findings"
echo "3. 📝 Copy .env.example to .env and configure with your values"
echo "4. 🚀 Push the changes to remove sensitive data from the remote repository"
echo
echo "📖 For credential rotation instructions, see:"
echo "   https://console.cloud.google.com/apis/credentials"