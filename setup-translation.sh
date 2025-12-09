#!/bin/bash
# Quick setup script for Google Translate API

echo "================================================"
echo "Google Translate API Setup for Medical Bot"
echo "================================================"
echo ""

# Check if API key already exists
if grep -q "GOOGLE_TRANSLATE_API_KEY" app/.env 2>/dev/null; then
    echo "✓ API key already configured in app/.env"
    echo ""
    read -p "Do you want to update it? (y/n): " update
    if [ "$update" != "y" ]; then
        echo "Keeping existing configuration."
        exit 0
    fi
fi

echo "Please follow these steps to get your API key:"
echo ""
echo "1. Go to: https://console.cloud.google.com/"
echo "2. Create or select a project"
echo "3. Enable 'Cloud Translation API' in APIs & Services > Library"
echo "4. Go to APIs & Services > Credentials"
echo "5. Click '+ CREATE CREDENTIALS' > 'API key'"
echo "6. Copy the generated API key"
echo ""
read -p "Enter your Google Translate API Key: " api_key

if [ -z "$api_key" ]; then
    echo "❌ No API key provided. Exiting."
    exit 1
fi

# Create or update .env file
mkdir -p app
if [ -f "app/.env" ]; then
    # Remove old key if exists
    sed -i '/GOOGLE_TRANSLATE_API_KEY/d' app/.env
fi

echo "GOOGLE_TRANSLATE_API_KEY=$api_key" >> app/.env

echo ""
echo "✓ API key saved to app/.env"
echo ""
echo "Restarting bot..."
docker compose restart fastapi

echo ""
echo "Waiting for bot to start..."
sleep 5

# Check logs
echo ""
echo "Checking bot status..."
docker logs medical-bot --tail 20 | grep -i "translate\|error" || echo "Bot started successfully!"

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Test the translation by sending messages in:"
echo "  • Amharic (አማርኛ): ራስ ይምታል"
echo "  • Afan Oromo: Mataan na dhukkuba"
echo "  • Tigrinya (ትግርኛ): ርእሲ የቐልዓለይ"
echo "  • Somali: Madax ayaa i xanuunaya"
echo ""
echo "The bot should respond in the same language!"
echo ""
