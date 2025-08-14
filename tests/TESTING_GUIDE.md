# CaliBOT Testing Procedures

## 🚨 MANDATORY PRE-TESTING PROCEDURES

### Step 1: Verify Latest Version Deployment
**CRITICAL**: Always verify the latest version is running before testing!

#### Quick Version Check
```bash
# Fast version comparison
python scripts/quick_version_check.py
```

#### Detailed Health Check
```bash
# Comprehensive verification with restart options
python scripts/verify_deployment.py
```

#### Manual Health Check
```bash
# Check current deployed version
curl -s https://calibot-utq6.onrender.com/health | python -m json.tool
```

Expected response should show the latest version from `pyproject.toml`:
```json
{
  "status": "healthy",
  "version": "0.1.121",
  "timestamp": "2024-12-19T..."
}
```

If version doesn't match your latest changes, proceed to Step 2.

### Step 2: Force Render Service Restart
**When to use**: If auto-deployment failed or version mismatch detected

#### Option A: Manual Restart via Render Dashboard
1. Visit [Render Dashboard](https://dashboard.render.com/)
2. Navigate to the `calibot` service
3. Click **"Manual Deploy"** or **"Restart"** button
4. Wait 2-3 minutes for deployment to complete
5. Re-verify version using Step 1

#### Option B: Force Deployment via Git Push
```bash
# Force a new deployment by creating an empty commit
git commit --allow-empty -m "Force deployment: trigger restart"
git push origin main
```

Wait 2-3 minutes, then verify version again.

### Step 3: Backend Health Check
**MANDATORY**: Always run before testing to ensure service is responsive

#### Automated Health Check
```bash
# Recommended: Use automated verification tool
python scripts/verify_deployment.py
```

#### Quick Manual Check
```bash
# Fast version and health verification
python scripts/quick_version_check.py
```

#### Manual Health Verification
```bash
# Quick health verification
python -c "
import requests
try:
    r = requests.get('https://calibot-utq6.onrender.com/health', timeout=10)
    print(f'✅ Backend Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'✅ Version: {data.get(\"version\", \"unknown\")}')
        print(f'✅ Health: {data.get(\"status\", \"unknown\")}')
    else:
        print(f'❌ Backend returned {r.status_code}')
except Exception as e:
    print(f'❌ Backend Error: {e}')
"
```

**Expected Output**:
```
✅ Backend Status: 200
✅ Version: 0.1.121
✅ Health: healthy
```

**If health check fails**:
1. Wait 2-3 minutes (service may be starting)
2. Try Step 2 (Force Restart)
3. Check Render dashboard for deployment errors
4. Review recent commits for breaking changes

---

## Automated Testing - Zero User Input Required

### Quick Start (Recommended)
```bash
cd tests
python telegram_like_tester.py
```

### One-by-One Workflow Testing (Critical)
```bash
cd tests
python test_one_by_one_workflow.py    # Specific testing for multi-event one-by-one processing
```

### Real Telegram Group Messages
```bash
cd tests
python quick_telegram_test.py          # Test setup first
python complete_telegram_simulator.py  # Full conversation demo
```

**Setup Required**:
1. Get your test bot token from @BotFather
2. Add your bot to your group chat
3. Get the group chat ID (negative number)
4. Edit the scripts or set environment variables:
   - `TELEGRAM_BOT_TOKEN=your_bot_token`
   - `TELEGRAM_GROUP_ID=your_group_chat_id`

**What you'll see in your Telegram group**:
- 👤 **TestUser**: Realistic user messages
- 🤖 **CaliBOT**: Bot responses with proper formatting
- 👆 **Button presses**: Inline keyboard interactions  
- 🔧 **System messages**: Scenario descriptions
- **All possible scenarios**: Creation, deletion, multi-event, confirmations, errors

This creates a complete bot-to-bot conversation demonstration!

#### Complete Scenario Coverage:
1. **Basic Interaction**: Greetings and calendar queries
2. **Event Creation**: Single event with success confirmation
3. **Multi-Event Creation**: Batch events with duplicate detection buttons
4. **Event Modification**: Moving events with confirmation buttons
5. **Event Deletion**: Deleting multiple events with selection buttons
6. **One-by-One Processing**: Critical workflow testing for individual event confirmations
7. **Calendar Selection**: AI suggestions with calendar choice buttons
8. **Error Handling**: Invalid input and recovery
9. **Complex Scheduling**: Rescheduling with time modifications
10. **Natural Conversation**: Complete workflow conversations

Each scenario includes realistic button interactions and confirmations!

### One-by-One Workflow Specific Testing

The `test_one_by_one_workflow.py` provides comprehensive testing for the critical "one by one" functionality:

#### Key Test Scenarios:
- **Update with Date and Time Changes**: Tests "move the last 2 lessons today to tomorrow 5 and 6 pm"
- **Delete Multiple Events**: Tests individual delete confirmations
- **Time Shift Updates**: Tests "move my next 2 meetings 1 hour later"
- **Event Renaming**: Tests batch renaming with individual confirmations
- **Calendar Movement**: Tests moving events between calendars

#### Expected Behavior Validation:
- ✅ Multi-event requests trigger confirmation options correctly
- ✅ "One by one" selection shows individual event details with proposed changes
- ✅ Each event processed independently with clear confirmation prompts
- ✅ No "operation not found" errors during workflow
- ✅ Complete workflow success for all events in queue

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
1. **Commit and push changes** to trigger deployment
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```
2. **MANDATORY: Wait for deployment** (2-3 minutes for Render auto-deploy)
3. **MANDATORY: Verify version deployment**:
   ```bash
   # Recommended: Use automated verification
   python scripts/verify_deployment.py
   
   # Or quick check:
   python scripts/quick_version_check.py
   ```
4. **If version mismatch**: Use automated restart in `verify_deployment.py` or manual procedures
5. **MANDATORY: Ensure backend is healthy** before testing
6. **Run automated tests**:
   ```bash
   cd tests
   python telegram_like_tester.py
   ```
7. **Analyze results** and iterate if needed
8. **Update CHANGELOG.md** with fixes and improvements

### 🚨 CRITICAL DEPLOYMENT RULES
- **NEVER test without version verification** - you may be testing old code
- **ALWAYS check health endpoint first** - saves time on failed tests
- **Force restart if auto-deploy fails** - Render doesn't always deploy automatically
- **Wait 2-3 minutes after push** - Render needs time to build and deploy
- **Check Render dashboard if issues persist** - may show deployment errors

### Troubleshooting Deployment Issues

#### Auto-Deployment Not Triggering
```bash
# Check if webhook is properly configured
git commit --allow-empty -m "Force deployment test"
git push origin main
```

#### Version Mismatch After Deployment
1. Check Render dashboard for deployment errors
2. Verify pyproject.toml version matches __init__.py version
3. Force manual deployment via Render dashboard
4. Check build logs for dependency issues

#### Service Not Responding After Deployment
1. Check Render service logs for startup errors
2. Verify environment variables are set correctly
3. Check for breaking changes in recent commits
4. Try restarting service via Render dashboard

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
- `scripts/verify_deployment.py` - **Automated deployment verification and restart**
- `scripts/quick_version_check.py` - **Fast version comparison**
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
