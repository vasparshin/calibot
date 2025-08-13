# Creating a Test Bot for Calibot Development

## Overview
This guide helps you create a separate test bot for development and debugging without interfering with your main bot.

## Step 1: Create a New Test Bot

1. **Message BotFather on Telegram**:
   ```
   /newbot
   ```

2. **Choose a name** (e.g., "Calibot Test"):
   ```
   Calibot Test
   ```

3. **Choose a username** (e.g., "calibot_test_dev_bot"):
   ```
   calibot_test_dev_bot
   ```

4. **Save the bot token** - you'll get something like:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

## Step 2: Set Up Test Environment

### Create Test Environment Variables
Create a `.env.test` file:
```bash
# Test Bot Configuration
TELEGRAM_BOT_TOKEN=your_test_bot_token_here
WEBHOOK_URL=https://your-test-app.onrender.com/webhook

# Use same Google Calendar API credentials
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://your-test-app.onrender.com/auth/callback

# Use same LLM configuration
LITELLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=your_openai_api_key
```

### Deploy Test Instance on Render
1. Create a new Render service
2. Connect to your GitHub repo
3. Use the same build/start commands
4. Set environment variables from `.env.test`
5. Use a different service name (e.g., `calibot-test`)

## Step 3: Automated Testing Scripts

I'll create automated testing scripts that can:
- Send messages to your test bot
- Monitor responses
- Check logs
- Validate functionality
- Run comprehensive test scenarios

## Step 4: Multi-User Chat Testing

### Create a Test Group
1. Create a new Telegram group
2. Add your test bot to the group
3. Add yourself and any collaborators
4. Test group interactions

### Test Scenarios
- Individual user interactions
- Group message handling
- Multiple calendar operations
- Error handling and recovery

## Benefits
- **Isolated Testing**: No interference with production bot
- **Automated Scenarios**: Run comprehensive tests without manual work
- **Real-time Debugging**: Monitor logs during automated testing
- **Safe Experimentation**: Test risky changes safely
- **Collaboration**: Multiple people can test simultaneously

## Next Steps
1. Create the test bot using BotFather
2. Set up test deployment on Render
3. Run automated test scenarios
4. Monitor and debug issues in real-time
