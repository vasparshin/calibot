#!/bin/bash
# Stream CaliBOT logs from Render.com in real-time
# Usage: ./scripts/stream_logs.sh

# Configuration
SERVICE_ID="srv-ctglj6qj1k6c73fpjbeg"  # CaliBOT service ID
LOGS_URL="https://api.render.com/v1/services/$SERVICE_ID/logs"

# Check if API key is set
if [ -z "$RENDER_API_KEY" ]; then
    echo "❌ RENDER_API_KEY environment variable not set"
    echo ""
    echo "📋 Setup Instructions:"
    echo "1. Get your API key from: https://dashboard.render.com/user/settings"
    echo "2. Set environment variable:"
    echo "   export RENDER_API_KEY='your_key_here'"
    echo "3. Run this script: ./scripts/stream_logs.sh"
    echo ""
    exit 1
fi

echo "🔄 Streaming logs from CaliBOT service: $SERVICE_ID"
echo "📡 API endpoint: $LOGS_URL"
echo "================================================================================"
echo "✅ Connected to Render log stream"
echo "🎯 Watching for CaliBOT activity..."
echo "-------------------------------------------------------------------------------"

# Stream logs using curl
curl -H "Authorization: Bearer $RENDER_API_KEY" \
     -H "Content-Type: application/json" \
     -N \
     "$LOGS_URL" | while IFS= read -r line; do
    # Add timestamp and color coding
    timestamp=$(date "+%H:%M:%S")
    
    # Color code important log types
    if [[ $line == *"🔍 LLM"* ]]; then
        echo "🔍 $timestamp | $line"
    elif [[ $line == *"🚨"* ]]; then
        echo "🚨 $timestamp | $line"
    elif [[ $line == *"ERROR"* ]]; then
        echo "❌ $timestamp | $line"
    elif [[ $line == *"Target"* ]] || [[ $line == *"target"* ]]; then
        echo "🎯 $timestamp | $line"
    elif [[ $line == *"Bot sending"* ]]; then
        echo "🤖 $timestamp | $line"
    else
        echo "📝 $timestamp | $line"
    fi
done
