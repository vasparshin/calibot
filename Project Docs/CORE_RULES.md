# CaliBOT Core Development Rules

## 🚨 CRITICAL INFO
- **Test Group ID**: `-4627994150` (NEVER LOSE)
- **Backend URL**: `https://calibot-utq6.onrender.com`
- **Version Source**: `pyproject.toml` and `backend/app/__init__.py`
- **Deploy**: Git push to main → auto-deploy to Render

## 🏗️ ARCHITECTURE
- **EventQueueHandler**: One-by-one event processing (CRITICAL)
- **MultiEventOperationHandler**: Batch operations
- **NLPAgent**: Intent extraction (GPT-4.1-mini)
- **GoogleCalendarService**: Calendar API + OAuth
- **TelegramBotService**: Message/webhook handling

## 🔧 WORKFLOW RULES
1. **Directory**: Always `cd calibot` first (project in subdirectory)
2. **Version**: Update `pyproject.toml` AND `backend/app/__init__.py`
3. **Testing**: `python scripts/quick_version_check.py` then `python tests/telegram_like_tester.py`
4. **Logs**: `python scripts/recent_logs.py` for debugging

## 🤖 BOT BEHAVIOR
- **Event Format**: `• [Name](link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar)`
- **Buttons**: MUST be temporary, removed after interaction with status text
- **One-by-one**: "DELETE Event X of Y" → button click → advance to "DELETE Event X+1 of Y"

## 🚨 ANTI-STUCK RULES (MANDATORY)
1. **NO ENDLESS DEBUGGING**: Max 2 debug iterations before fixing root cause directly
2. **NO DEPLOYMENT WAITING**: Deploy only when you have a concrete fix, not for debugging
3. **FIX THE ACTUAL PROBLEM**: Don't add logging - analyze the code and fix the logic
4. **SYSTEMATIC APPROACH**: Identify root cause first, then implement targeted fix

## 🚨 CURRENT CRITICAL ISSUE
**One-by-one logic broken**: "Yes" button processed but system sends full event list instead of Event 2
