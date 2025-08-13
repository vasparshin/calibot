# CaliBOT Testing Procedures

## Automated Testing - Zero User Input Required

### Quick Start (Recommended)
```bash
cd tests
python telegram_like_tester.py
```

### Real Telegram Group Messages
```bash
cd tests
python simple_group_poster.py
```

**Setup Required**:
1. Get your test bot token from @BotFather
2. Add your bot to your group chat
3. Get the group chat ID (negative number)
4. Edit `simple_group_poster.py` or set environment variables:
   - `TELEGRAM_BOT_TOKEN=your_bot_token`
   - `TELEGRAM_GROUP_ID=your_group_chat_id`

This posts actual messages to your Telegram group showing realistic bot conversations!

This provides the best testing experience:
- **Visual Telegram-like chat interface** showing user messages and bot responses
- **Fully automated** - no user input required  
- **Real-world simulation** with realistic conversation flow
- **Comprehensive coverage** of all critical functionality
- **Easy to understand** progress and results

### Advanced Testing (Backend Analysis)
```bash
cd tests
python backend_bridge_tester.py
```

This provides detailed technical analysis:
- **Direct webhook testing** bypassing Telegram limitations
- **Comprehensive test suite** with edge cases
- **Technical debugging information**
- **JSON result files** for detailed analysis

## Testing Architecture

### 1. Telegram-Like Visual Testing (`telegram_like_tester.py`)
**Purpose**: Simulate real user conversations visually
**Best For**: 
- Understanding bot behavior from user perspective
- Visual verification of fixes and improvements  
- Demonstrating functionality to stakeholders
- Quick validation of user experience

**Features**:
- Chat-like interface with timestamps
- User messages and bot responses clearly separated
- System messages for debugging context
- Success/failure indicators with emojis
- Conversation flow that mirrors real usage

### 2. Backend Bridge Testing (`backend_bridge_tester.py`)  
**Purpose**: Technical validation of backend functionality
**Best For**:
- Debugging specific intent extraction issues
- Comprehensive edge case testing
- Performance and reliability analysis
- Detailed technical validation

**Features**:
- Direct webhook payload simulation
- Bypasses Telegram bot-to-bot limitations
- Comprehensive test coverage
- Detailed JSON result logging
- Technical error analysis

## Configuration

### Backend URL
Both testers are pre-configured with the current production URL:
```
https://calibot-utq6.onrender.com
```

**No manual configuration required** - testers automatically use the correct backend.

### Test Data
Tests use realistic scenarios that cover:
- **Intent Extraction**: Event creation, modification, deletion, queries
- **Calendar Selection**: AI-driven and rule-based calendar selection
- **Multi-Event Operations**: Batch operations with confirmations
- **Edge Cases**: Complex scheduling, date parsing, error handling
- **User Experience**: Natural language variations and conversation flow

## Test Categories

### Critical Intent Extraction Tests
1. **"move the last 2 events of today to tomorrow"** - Tests update intent recognition
2. **"show me tomorrow's schedule"** - Tests query intent recognition  
3. **"create an event called 'Meeting' tomorrow at 3pm"** - Tests create intent
4. **"delete my last meeting"** - Tests delete intent

### Real-World Conversation Flow  
1. **Greeting and context establishment**
2. **Basic calendar queries**
3. **Event creation and modification**
4. **Batch operations**
5. **Error handling and edge cases**
6. **Natural conversation closure**

### Edge Cases
- Complex rescheduling operations
- Multiple event modifications
- Date range queries
- Error scenarios and recovery

## Result Analysis

### Success Metrics
- **≥80%**: Excellent - ready for production use
- **60-79%**: Good - minor fixes needed
- **<60%**: Needs attention - significant issues detected

### Key Indicators
- **Intent extraction accuracy**: Are user commands classified correctly?
- **Response consistency**: Do responses follow BOT_RULES.md formatting?
- **Error handling**: Are failures graceful with helpful messages?
- **Conversation flow**: Does the bot maintain context appropriately?

## Troubleshooting

### Common Issues

#### Backend Not Responding (502 errors)
```bash
# Check deployment status
cd scripts
python list_services.py
```

#### Intent Extraction Failures
Look for these patterns in test results:
- Messages classified as wrong intent type
- Schedule service intercepting modification requests
- LLM parsing errors in JSON responses

#### Response Formatting Issues
Check for:
- Missing calendar names in event displays
- Inconsistent date/time formatting
- Missing hyperlinks or formatting errors

### Log Analysis
```bash
# Check recent logs for debugging
cd scripts  
python simple_logs.py
```

## Development Workflow

### After Making Code Changes:
1. **Commit changes** to trigger deployment
2. **Wait 30-60 seconds** for Render deployment
3. **Run automated tests**:
   ```bash
   cd tests
   python telegram_like_tester.py
   ```
4. **Analyze results** and iterate if needed
5. **Update CHANGELOG.md** with fixes and improvements

### Continuous Testing
Run tests regularly during development:
- **After each significant change**
- **Before committing fixes**  
- **After deployment to production**
- **When debugging user-reported issues**

## File Locations

### Test Files
- `tests/telegram_like_tester.py` - Visual conversation testing
- `tests/backend_bridge_tester.py` - Technical backend testing
- `tests/auto_url_finder.py` - Backend URL discovery

### Result Files
- `telegram_simulation_*.json` - Visual test results
- `automated_test_*.json` - Backend test results
- `comprehensive_test_*.json` - Full test suite results

### Supporting Tools
- `scripts/list_services.py` - Check deployment status
- `scripts/simple_logs.py` - View recent logs
- `scripts/stream_logs.py` - Real-time log monitoring

## Security Notes

- **Test data is isolated** - uses dedicated test chat IDs
- **No real user data affected** - all tests use mock/test accounts
- **Production-safe** - tests don't modify real user calendars
- **Webhook simulation** - tests exact production code paths safely

---

**Recommendation**: Always start with `telegram_like_tester.py` for the best testing experience. It provides the most intuitive view of bot behavior and is perfect for validating user-facing improvements.
