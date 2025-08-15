# CaliBOT Planned Features

This document tracks features planned for implementation in the CaliBOT project. Each feature includes analysis of implementation approach based on current architecture.

## 🎯 Feature Pipeline

### 1. Voice to Text Messages
**Priority**: High  
**Status**: Planned  
**Description**: Allow users to send voice messages that are automatically converted to text for calendar operations.

**Implementation Analysis**:
- **Integration Point**: Telegram Bot API supports voice message handling via `voice` message type
- **Technology**: Use Telegram's built-in voice-to-text or integrate with services like OpenAI Whisper API
- **Architecture Impact**: 
  - Extend `routes.py` webhook handler to process `voice` message types
  - Add voice processing service in `app/services/voice_service.py`
  - Update NLP agent to handle transcribed text with confidence scoring
- **Dependencies**: OpenAI Whisper API or Telegram's voice processing
- **Estimated Effort**: Medium (2-3 days)

### 2. Multi-User Appointment Booking
**Priority**: High  
**Status**: Planned  
**Description**: Enable secondary users to book appointments on primary user's calendar based on availability, with approval workflow.

**Implementation Analysis**:
- **User Management**: 
  - Add user roles system: `primary_user`, `secondary_user`
  - Store user permissions in database/config
  - Implement authorization middleware
- **Availability Logic**:
  - Query primary user's calendar for free time slots
  - Calculate availability windows (e.g., 9 AM - 5 PM, excluding existing events)
  - Return formatted availability options
- **Approval Workflow**:
  - Queue appointment requests for primary user approval
  - Extend `multi_event_operations.py` for approval/rejection flow
  - Add notification system for pending requests
- **Architecture Changes**:
  - New service: `app/services/availability_service.py`
  - New service: `app/services/approval_workflow_service.py`
  - Database: User relationships and pending requests
  - Extend conversation state to track approval contexts
- **Dependencies**: User authentication system, database for request tracking
- **Estimated Effort**: High (5-7 days)

### 3. Google Calendar Availability Integration
**Priority**: Medium  
**Status**: Planned  
**Description**: Incorporate user's existing availability schedule and busy/free status from Google Calendar.

**Implementation Analysis**:
- **Google Calendar API**: 
  - Use `freebusy` API to query availability
  - Parse working hours from calendar settings
  - Respect existing event blocks as unavailable
- **Integration Points**:
  - Extend `GoogleCalendarService` with availability methods
  - Cache availability data for performance
  - Update calendar agent to consider availability in suggestions
- **Architecture Impact**:
  - New methods in `google_calendar.py`: `get_availability()`, `check_free_busy()`
  - Availability caching mechanism
  - Integration with appointment booking feature
- **Dependencies**: Enhanced Google Calendar API permissions
- **Estimated Effort**: Medium (3-4 days)

### 4. Document Auto-Recognition (PDFs, Images)
**Priority**: Medium  
**Status**: Planned  
**Description**: Process uploaded PDFs and documents to automatically extract event information.

**Implementation Analysis**:
- **Document Processing**:
  - PDF text extraction: PyPDF2 or pdfplumber
  - Image OCR: Tesseract or Google Vision API
  - Document parsing for date/time patterns
- **Integration Strategy**:
  - Extend webhook handler for `document` message types
  - New service: `app/services/document_processor.py`
  - Use existing NLP agent for intent extraction from document text
- **Architecture Changes**:
  - File download and temporary storage handling
  - Document type detection and routing
  - Error handling for corrupted/unreadable documents
- **Dependencies**: OCR libraries, file storage mechanism
- **Estimated Effort**: Medium (4-5 days)

### 5. Gmail Integration for Event Processing
**Priority**: Medium  
**Status**: Planned  
**Description**: Monitor Gmail for emails containing event information and suggest calendar entries.

**Implementation Analysis**:
- **Gmail API Integration**:
  - OAuth scope expansion for Gmail access
  - Email filtering and monitoring system
  - Parse email content for event patterns
- **Event Detection**:
  - Email subject/body analysis for date/time patterns
  - Meeting invitation detection
  - Confirmation email parsing (flights, reservations, etc.)
- **Architecture Impact**:
  - New service: `app/services/gmail_service.py`
  - Email content preprocessing for NLP agent
  - Background job system for email monitoring
  - User notification system for suggested events
- **Dependencies**: Gmail API access, background job scheduler
- **Estimated Effort**: High (6-8 days)

### 6. Google Sheets Calendar Export
**Priority**: Low  
**Status**: Planned  
**Description**: Export calendar data to Google Sheets in tabular format with dates as rows.

**Implementation Analysis**:
- **Google Sheets API**:
  - Create/update spreadsheets with calendar data
  - Format dates as rows, events as columns
  - Auto-refresh mechanism for data sync
- **Export Logic**:
  - Query calendar events for specified date range
  - Format data in tabular structure
  - Handle recurring events and time zones
- **Integration Points**:
  - New intent type: "export_calendar"
  - Extend `GoogleCalendarService` with Sheets integration
  - User-configurable export templates
- **Dependencies**: Google Sheets API, export formatting logic
- **Estimated Effort**: Medium (3-4 days)

### 7. Event Reminders via Bot
**Priority**: High  
**Status**: Planned  
**Description**: Send automated reminders for upcoming events through Telegram bot.

**Implementation Analysis**:
- **Reminder System**:
  - Background scheduler (APScheduler or Celery)
  - Query upcoming events with reminder preferences
  - Send Telegram notifications at specified intervals
- **User Preferences**:
  - Configurable reminder times (15 min, 1 hour, 1 day before)
  - Event-specific reminder settings
  - Snooze and dismiss functionality
- **Architecture Changes**:
  - New service: `app/services/reminder_service.py`
  - Background job scheduler integration
  - User preference storage system
  - Reminder state management
- **Dependencies**: Background job system, persistent storage
- **Estimated Effort**: Medium (4-5 days)

## 🐛 Current Issues to Fix

#

## 📋 Implementation Priority Order

1. **Fix Current Update Issues** (Critical - Immediate)
2. **Voice to Text** (High Value, Lower Complexity)
3. **Event Reminders** (High User Value)
4. **Multi-User Booking** (High Business Value)
5. **Availability Integration** (Enables booking feature)
6. **Document Processing** (Medium Value)
7. **Gmail Integration** (Advanced Feature)
8. **Sheets Export** (Nice to Have)

## 🔄 Feature Request Workflow

When new features are requested:
1. Add to this document with implementation analysis
2. Assess impact on current architecture
3. Identify dependencies and integration points
4. Estimate development effort
5. Prioritize based on user value and complexity
6. Update CHANGELOG.md when implemented

---

*This document should be consulted before implementing any new features to ensure architectural consistency and proper planning.*
