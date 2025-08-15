# CaliBOT 📅 - Project Documentation

CaliBOT is an intelligent Telegram bot that helps users manage their Google Calendar through natural language conversations. The bot leverages GPT-4.1-mini for natural language understanding and implements a sophisticated multi-agent architecture.

## ✨ Features

- 🗓️ **Calendar Management**: Create, update, delete, and query calendar events using conversational language
- 🤖 **AI-Powered**: Utilizes GPT-4.1-mini for natural language understanding and conversation management
- 🔄 **Google Calendar Integration**: Securely connects to users' Google Calendar accounts
- 💬 **Contextual Conversations**: Maintains conversation history to provide relevant responses
- 🧠 **Intent Recognition**: Automatically identifies calendar-related requests vs. small talk
- 🔐 **Secure Authentication**: OAuth 2.0 integration with Google Calendar API
- 🚀 **Multi-Event Operations**: Advanced batch processing for creating, updating, and deleting multiple events

## 📋 Documentation Structure

### Core Project Files
- **`BOT_RULES.md`** - User interface formatting rules and behavior standards
- **`CHANGELOG.md`** - Complete version history and change documentation  
- **`PROJECT_RULES.md`** - Development guidelines, deployment procedures, and critical information
- **`PLANNED_FEATURES.md`** - Feature roadmap and implementation analysis
- **`WORKFLOW_ARCHITECTURE.md`** - System design and architecture documentation
- **`B2B_DEMO_AUTOMATION.md`** - Bot-to-Bot automated testing framework documentation

### Project Overview
- **`README.md`** - This file - Complete project description and documentation index

## 🚨 Critical Information

### Your Group Chat ID
**NEVER LOSE THIS**: `-4627994150` (documented in PROJECT_RULES.md)

### Bot-to-Bot Demo Protocol
Comprehensive testing procedure documented in PROJECT_RULES.md:
- TestBot frontend messages + CaliBOT webhook backend
- Live log monitoring via Render API
- Automated button press simulation
- All scenario combinations tested
- Zero user input required

## 📁 File Organization Rules

### What Belongs Here
- Project-level documentation
- Development guidelines
- Architecture specifications
- Change history
- Feature planning

### What Does NOT Belong Here
- Test files (`tests/` folder)
- Scripts (`scripts/` folder)
- Source code (`backend/` folder)
- Configuration files (project root)

## 🔗 References

This folder is referenced in:
- `.github/copilot-instructions.md` - For AI development guidance
- `tests/README.md` - For testing protocol references
- `scripts/README.md` - For utility script documentation

## 📝 Maintenance

All files in this folder should be:
- Keep up to date with project changes
- Referenced in changelog when modified
- Version controlled with descriptive commit messages
- Written in clear, professional markdown format
