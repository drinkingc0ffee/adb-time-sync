#!/bin/bash
# GitHub Upload Helper Script

echo "🚀 GitHub Upload Helper for ADB Time Sync"
echo "=========================================="
echo ""

# Check if git is configured
if ! git config --global user.name > /dev/null 2>&1; then
    echo "❌ Git user.name not configured"
    echo "Run: git config --global user.name 'Your Name'"
    exit 1
fi

if ! git config --global user.email > /dev/null 2>&1; then
    echo "❌ Git user.email not configured"
    echo "Run: git config --global user.email 'your.email@example.com'"
    exit 1
fi

echo "✅ Git configuration looks good!"
echo "Username: $(git config --global user.name)"
echo "Email: $(git config --global user.email)"
echo ""

echo "📋 Steps to upload to GitHub:"
echo "1. Go to https://github.com/new"
echo "2. Repository name: adb-time-sync"
echo "3. Description: ADB Time Sync tool with NTP synchronization"
echo "4. Choose Public or Private"
echo "5. DO NOT initialize with README, .gitignore, or license"
echo "6. Click 'Create repository'"
echo ""

echo "🔗 After creating the repository, run one of these commands:"
echo ""
echo "For HTTPS (recommended):"
echo "git remote add origin https://github.com/$(git config --global user.name)/adb-time-sync.git"
echo ""
echo "For SSH (if you have SSH keys set up):"
echo "git remote add origin git@github.com:$(git config --global user.name)/adb-time-sync.git"
echo ""
echo "Then push your code:"
echo "git branch -M main"
echo "git push -u origin main"
echo ""

echo "💡 Quick copy-paste commands (replace YOUR_USERNAME with your GitHub username):"
echo "git remote add origin https://github.com/YOUR_USERNAME/adb-time-sync.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""

echo "🎉 After pushing, your repository will be available at:"
echo "https://github.com/YOUR_USERNAME/adb-time-sync" 