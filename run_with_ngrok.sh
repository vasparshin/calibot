#!/bin/bash

# Start ngrok in the background
ngrok http 8060 > /dev/null &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get the public URL from ngrok's API
NGROK_URL=""
while [ -z "$NGROK_URL" ]; do
  NGROK_URL=$(curl --silent http://127.0.0.1:4040/api/tunnels | grep -o 'https://[0-9a-z]*\.ngrok-free\.app')
  sleep 1
done

echo "ngrok URL: $NGROK_URL"

# Update .env file (replace the BACKEND_URL line)
sed -i "s|^BACKEND_URL=.*|BACKEND_URL=$NGROK_URL|" backend/app/.env

# Start the FastAPI server
cd backend
python -m app.main

# When done, kill ngrok
kill $NGROK_PID