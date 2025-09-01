"""
Optimized routes.py using the new operation-based architecture.
Significantly reduced from 1444 lines to a focused, maintainable implementation.
"""

from fastapi import APIRouter, Request, HTTPException
import os
from datetime import datetime
import logging
from typing import Dict, List

from app import __version__

from app.config import GOOGLE_CLIENT_SECRET_FILE, GOOGLE_API_SCOPES
from app.services.telegram import (
    TelegramBotService,
    send_telegram_message,
    answer_callback_query,
    edit_message_text
)
from app.services.google_calendar import GoogleCalendarService
from app.services.conversation import conversation_state
from app.agent.nlp_agent import NLPAgent
from app.agent.calendar_agent import CalendarAgent
from app.core.confirmation_handler import ConfirmationHandler
from app.core.response_manager import ResponseManager
from app.operations.operation_factory import OperationFactory

# Initialize services
router = APIRouter()
telegram_service = TelegramBotService()
calendar_service = GoogleCalendarService()
calendar_agent = CalendarAgent()
ai_agent = NLPAgent()
confirmation_handler = ConfirmationHandler(telegram_service, conversation_state, calendar_service)
response_manager = ResponseManager()
operation_factory = OperationFactory(telegram_service, conversation_state, calendar_service, calendar_agent)

logger = logging.getLogger(__name__)

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram messages and callback queries."""
    try:
        update_data = await request.json()
        logger.debug(f"Received Telegram update: {update_data}")

        # Handle callback queries (inline keyboard button presses)
        if "callback_query" in update_data:
            return await handle_callback_query(update_data["callback_query"])

        # Handle regular messages
        if "message" not in update_data:
            return {"status": "ok"}

        message = update_data["message"]
        chat_id = message["chat"]["id"]

        if "text" not in message:
            await send_telegram_message(chat_id, "I'm sorry, I didn't understand that. Can you please rephrase your message?")
            return {"status": "ok"}

        user_message = message["text"]
        logger.info(f"👤 User message from chat {chat_id}: '{user_message}'")

        # Process the message
        return await process_user_message(chat_id, user_message)

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

async def handle_callback_query(callback_query):
    """Handle inline keyboard button presses."""
    try:
        chat_id = callback_query["message"]["chat"]["id"]
        message_id = callback_query["message"]["message_id"]
        callback_data = callback_query.get("data", "")
        callback_query_id = callback_query["id"]

        logger.info(f"🔘 Callback query from chat {chat_id}: {callback_data}")

        # Always answer to stop Telegram spinner
        await answer_callback_query(callback_query_id, "Processing...")

        # Handle different callback types
        if callback_data.startswith("confirm_"):
            return await handle_confirmation_callback(chat_id, message_id, callback_data)
        elif callback_data.startswith("queue_"):
            return await handle_queue_callback(chat_id, message_id, callback_data)
        elif callback_data.startswith("schedule_"):
            return await handle_schedule_callback(chat_id, message_id, callback_data)
        elif callback_data == "update_one_by_one":
            return await handle_multi_event_callback(chat_id, message_id, callback_data)
        elif callback_data.startswith("confirm_update_"):
            return await handle_multi_event_callback(chat_id, message_id, callback_data)
        else:
            logger.warning(f"Unknown callback data: {callback_data}")
            return {"status": "ok"}

    except Exception as e:
        logger.error(f"Callback query error: {e}")
        return {"status": "error", "message": str(e)}

async def handle_confirmation_callback(chat_id: int, message_id: int, callback_data: str):
    """Handle confirmation callbacks."""
    try:
        # Parse confirmation type
        confirmation = callback_data.replace("confirm_", "")

        # Use confirmation handler
        await confirmation_handler.handle_single_confirmation(chat_id, message_id, confirmation == "yes")

        # Process the confirmation through operation factory
        result = await operation_factory.handle_confirmation(chat_id, confirmation, {})

        if result.get("requires_user_action"):
            # Send follow-up message if needed
            await confirmation_handler.send_follow_up_message(
                chat_id,
                result.get("message", "Processing..."),
                result.get("keyboard")
            )

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Confirmation callback error: {e}")
        return {"status": "error"}

async def handle_queue_callback(chat_id: int, message_id: int, callback_data: str):
    """Handle queue navigation callbacks."""
    try:
        # Parse queue action
        action = callback_data.replace("queue_", "")

        # Use confirmation handler for queue actions
        await confirmation_handler.handle_queue_confirmation(chat_id, message_id, action)

        # Process through operation factory (would need queue-specific handling)
        # For now, return success
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Queue callback error: {e}")
        return {"status": "error"}

async def handle_schedule_callback(chat_id: int, message_id: int, callback_data: str):
    """Handle schedule button callbacks."""
    try:
        # Parse schedule type
        schedule_type = callback_data.replace("schedule_", "")

        # Remove keyboard from original message
        await edit_message_text(chat_id, message_id, "📅 Loading schedule...", reply_markup={})

        # Handle schedule request
        result = await handle_schedule_request(chat_id, schedule_type)

        # Send result as new message
        if result.get("success"):
            await send_telegram_message(chat_id, result["message"])
        else:
            error_msg = result.get("message", "Failed to get schedule")
            await send_telegram_message(chat_id, error_msg)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Schedule callback error: {e}")
        return {"status": "error"}

async def handle_multi_event_callback(chat_id: int, message_id: int, callback_data: str):
    """Handle multi-event operation callbacks."""
    try:
        # Use confirmation handler for multi-event operations
        if callback_data == "update_one_by_one":
            await confirmation_handler.handle_multi_confirmation(chat_id, message_id, "one", "update")
        elif callback_data.startswith("confirm_update_"):
            # Extract confirmation number and handle as single confirmation
            parts = callback_data.split("_")
            if len(parts) >= 3 and parts[-1].isdigit():
                confirmation_num = int(parts[-1])
                confirmed = parts[1] == "update"  # This might need adjustment based on actual logic
                await confirmation_handler.handle_single_confirmation(chat_id, message_id, confirmed, f"update event {confirmation_num}")
        else:
            logger.warning(f"Unhandled multi-event callback: {callback_data}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Multi-event callback error: {e}")
        return {"status": "error"}

async def process_user_message(chat_id: int, user_message: str):
    """Process user message through the optimized pipeline."""
    try:
        # Check authentication
        if not await check_authentication(chat_id):
            return {"status": "ok"}

        # Add message to conversation
        conversation_state.add_message(chat_id, "user", user_message)

        # Handle schedule requests first
        schedule_result = await handle_schedule_request(chat_id, user_message)
        if schedule_result:
            # Actually send the schedule response to Telegram
            if schedule_result.get("success"):
                await send_telegram_message(chat_id, schedule_result["message"])
            else:
                error_msg = schedule_result.get("message", "Failed to get schedule")
                await send_telegram_message(chat_id, error_msg)
            return {"status": "ok"}

        # Extract intent using NLP agent
        history = conversation_state.get_conversation_history(chat_id)
        intent_result = await ai_agent.extract_intent(user_message, history)

        if not intent_result or not isinstance(intent_result, dict):
            await send_telegram_message(chat_id, "Sorry, I had trouble understanding your request. Could you please try again?")
            return {"status": "ok"}

        # Debug logging for operation execution
        logger.info(f"🎯 Executing operation for intent: {intent_result.get('intent')}")
        logger.info(f"🎯 Intent data: {intent_result}")

        # Execute operation through factory
        result = await operation_factory.execute_operation(chat_id, intent_result)

        # Debug logging for operation result
        logger.info(f"📊 Operation result: success={result.get('success')}, requires_llm={result.get('requires_llm_formatting')}, requires_action={result.get('requires_user_action')}")

        # Handle result
        if result.get("requires_llm_formatting"):
            # LLM-driven query result - pass data back to LLM for final response formatting
            await handle_llm_formatted_query(chat_id, intent_result, result, history)
        elif result.get("requires_user_action"):
            # Send message with keyboard if needed
            keyboard = result.get("keyboard")
            if keyboard:
                await send_telegram_message(chat_id, result["message"], reply_markup=keyboard)
            else:
                await send_telegram_message(chat_id, result["message"])
        elif result.get("success"):
            # Send success message
            await send_telegram_message(chat_id, result["message"])
        else:
            # Send error message
            error_msg = result.get("message", "An error occurred while processing your request.")
            await send_telegram_message(chat_id, error_msg)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Message processing error: {e}")
        await send_telegram_message(chat_id, "I'm experiencing technical difficulties. Please try again in a moment.")
        return {"status": "error"}

async def handle_llm_formatted_query(chat_id: int, original_intent: Dict, query_result: Dict, conversation_history: List):
    """Handle LLM-driven query results by passing data back to LLM for final response formatting."""
    try:
        # Extract query data
        query_data = query_result.get("query_result", {})

        # Check for authentication requirement
        if query_data.get("auth_required"):
            auth_message = "Please authenticate with Google Calendar first: /start"
            await send_telegram_message(chat_id, auth_message)
            return

        # Format events data for LLM
        events_data = format_events_for_llm(query_data.get("events", []))
        query_params = query_data.get("query_params", {})

        # Create LLM prompt for response formatting
        formatting_prompt = f"""
You received this query from the user: "{original_intent.get('original_message', '')}"

I retrieved the following calendar data:
{events_data}

Query parameters used: {query_params}

Based on the user's request and the retrieved data, provide a natural, helpful response.
If no events were found, explain this clearly and suggest alternatives if appropriate.

CRITICAL: Format ALL events using this EXACT format (MANDATORY):
• [Event Name](calendar_link) on Day, Month DD, YYYY at HH:MM AM/PM - HH:MM AM/PM (Calendar Name)

Examples:
• [Math Lesson](https://calendar.google.com/calendar/event?eid=abc123) on Monday, September 02, 2025 at 09:00 AM - 10:00 AM (Personal)
• [Team Meeting](https://calendar.google.com/calendar/event?eid=def456) on Tuesday, September 03, 2025 at 02:00 PM - 03:00 PM (Work)

RULES:
- ALWAYS use bullet points (•)
- ALWAYS create hyperlinks with [Event Name](link)
- ALWAYS use full date format: Day, Month DD, YYYY
- ALWAYS use 12-hour time format with AM/PM
- ALWAYS include calendar name in parentheses
- Use the Link field from the event data for hyperlinks

Return only the response message that should be sent to the user.
"""

        # Get LLM response
        try:
            llm_response = await ai_agent.generate_response(formatting_prompt, conversation_history)
            if llm_response and llm_response.strip():
                await send_telegram_message(chat_id, llm_response.strip())
            else:
                await send_telegram_message(chat_id, "I found some information but couldn't format it properly. Please try rephrasing your request.")
        except Exception as llm_error:
            logger.error(f"LLM formatting error: {llm_error}")
            # Fallback: provide basic formatted response
            await send_basic_query_response(chat_id, query_data)

    except Exception as e:
        logger.error(f"Error in LLM formatted query: {e}")
        await send_telegram_message(chat_id, "I encountered an error while processing your query. Please try again.")

def format_events_for_llm(events: List[Dict]) -> str:
    """Format events data for LLM consumption."""
    if not events:
        return "No events found matching the query criteria."

    formatted_events = []
    for i, event in enumerate(events, 1):
        event_info = f"""
Event {i}:
- Title: {event.get('summary', 'Untitled')}
- Start: {event.get('start', 'Unknown')}
- End: {event.get('end', 'Unknown')}
- Calendar: {event.get('calendar_name', 'Unknown')}
- Link: {event.get('link', 'N/A')}
"""
        formatted_events.append(event_info)

    return f"Found {len(events)} event(s):\n" + "\n".join(formatted_events)

async def send_basic_query_response(chat_id: int, query_data: Dict):
    """Send a basic formatted response when LLM formatting fails."""
    try:
        events = query_data.get("events", [])
        event_count = query_data.get("event_count", 0)

        if event_count == 0:
            await send_telegram_message(chat_id, "No events found matching your query.")
        elif event_count == 1:
            event = events[0]
            message = f"Found 1 event:\n\n{event.get('summary', 'Untitled')} at {event.get('start', 'Unknown time')}"
            await send_telegram_message(chat_id, message)
        else:
            message = f"Found {event_count} events:\n\n"
            for i, event in enumerate(events[:5], 1):  # Show first 5 events
                message += f"{i}. {event.get('summary', 'Untitled')} at {event.get('start', 'Unknown time')}\n"
            if event_count > 5:
                message += f"\n... and {event_count - 5} more events"
            await send_telegram_message(chat_id, message)
    except Exception as e:
        logger.error(f"Error in basic query response: {e}")
        await send_telegram_message(chat_id, "I found some events but had trouble formatting the response.")

async def check_authentication(chat_id: int) -> bool:
    """Check if user is authenticated and handle auth flow."""
    try:
        auth_check = calendar_service.is_authenticated()

        if not auth_check:
            try:
                auth_url = calendar_service.get_auth_url(force_fresh=True)
                await send_telegram_message(
                    chat_id,
                    f"To use this bot, please authenticate your Google account: [Click here]({auth_url})\n\n"
                    f"If you encounter any authentication errors, please check the OAuth configuration or contact support."
                )
            except ValueError as ve:
                logger.error(f"OAuth configuration error: {ve}")
                await send_telegram_message(
                    chat_id,
                    "❌ Authentication system is not properly configured. Please contact the administrator.\n\n"
                    f"Error details: {str(ve)}"
                )
            except Exception as e:
                logger.error(f"Unexpected authentication error: {e}")
                await send_telegram_message(
                    chat_id,
                    "❌ Authentication system is temporarily unavailable. Please try again later or contact support.\n\n"
                    "For immediate assistance, visit: https://calibot-utq6.onrender.com/auth/status"
                )
            return False

        return True

    except Exception as e:
        logger.error(f"Authentication check error: {e}")
        await send_telegram_message(chat_id, "Authentication system error. Please try again later.")
        return False

async def handle_schedule_request(chat_id: int, request: str) -> dict:
    """Handle schedule-related requests."""
    try:
        # Use schedule service if available
        from app.services.schedule_service import ScheduleService
        schedule_service = ScheduleService(calendar_service)

        schedule_type = schedule_service.detect_schedule_query(request)

        if schedule_type:
            if schedule_type == "today":
                result = await schedule_service.get_today_schedule(chat_id)
            elif schedule_type == "tomorrow":
                result = await schedule_service.get_tomorrow_schedule(chat_id)
            elif schedule_type in ["day after tomorrow", "next week"]:
                result = await schedule_service.get_schedule_for_relative_date(schedule_type, chat_id)
            else:
                return None

            if result.get("success"):
                return {
                    "success": True,
                    "message": result["message"],
                    "handled": True
                }
            else:
                error_msg = result.get("message", "Failed to get schedule")
                if result.get("auth_required"):
                    error_msg = "Please authenticate with Google Calendar first: /start"
                return {
                    "success": False,
                    "message": error_msg,
                    "handled": True
                }

        return None

    except Exception as e:
        logger.error(f"Schedule request error: {e}")
        return {
            "success": False,
            "message": "Sorry, there was an error loading your schedule.",
            "handled": True
        }

# OAuth endpoints (unchanged)
@router.get("/oauth2callback")
async def oauth_callback(request: Request):
    """Handle Google OAuth callback."""
    logger.info(f"Received OAuth callback with code: {request.query_params.get('code')}")
    return await calendar_service.handle_oauth_callback(request)

@router.get("/auth/status")
async def auth_status():
    """Check authentication status and OAuth configuration"""
    try:
        status = {
            "authenticated": calendar_service.is_authenticated(),
            "credentials_file_configured": bool(GOOGLE_CLIENT_SECRET_FILE),
            "credentials_file_exists": bool(GOOGLE_CLIENT_SECRET_FILE and os.path.exists(GOOGLE_CLIENT_SECRET_FILE)),
            "redirect_uri": calendar_service.redirect_uri,
            "scopes": GOOGLE_API_SCOPES
        }

        # Add OAuth client configuration details
        if GOOGLE_CLIENT_SECRET_FILE and os.path.exists(GOOGLE_CLIENT_SECRET_FILE):
            try:
                import json
                with open(GOOGLE_CLIENT_SECRET_FILE, 'r') as f:
                    client_config = json.load(f)

                if 'web' in client_config:
                    web_config = client_config['web']
                    status["oauth_client_type"] = "web"
                    status["client_id"] = web_config.get('client_id', 'Not found')
                    status["configured_redirect_uris"] = web_config.get('redirect_uris', [])
                    status["redirect_uri_match"] = calendar_service.redirect_uri in web_config.get('redirect_uris', [])
                else:
                    status["oauth_client_type"] = "unknown"
                    status["error"] = "OAuth client not configured as 'Web application'"

            except Exception as e:
                status["credentials_file_error"] = str(e)

        if not status["authenticated"]:
            try:
                auth_url = calendar_service.get_auth_url(force_fresh=True)
                status["auth_url"] = auth_url
            except Exception as e:
                status["auth_error"] = str(e)

        return status
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return {"error": str(e)}

@router.get("/auth/login")
async def login():
    """Initiate OAuth login flow"""
    try:
        if calendar_service.is_authenticated():
            return {"message": "Already authenticated", "authenticated": True}

        auth_url = calendar_service.get_auth_url(force_fresh=True)
        return {"auth_url": auth_url, "message": "Please visit the auth_url to authenticate"}
    except ValueError as ve:
        logger.error(f"OAuth configuration error in login endpoint: {ve}")
        raise HTTPException(
            status_code=500,
            detail=f"OAuth configuration error: {str(ve)}. Please ensure the OAuth client is configured as 'Web application' in Google Cloud Console."
        )
    except Exception as e:
        logger.error(f"Error initiating login: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate login: {str(e)}")

@router.get("/auth/fresh")
async def get_fresh_auth_url():
    """Get a guaranteed fresh OAuth authentication URL with cache-busting"""
    try:
        if calendar_service.is_authenticated():
            return {
                "message": "Already authenticated",
                "authenticated": True,
                "fresh_auth_url": calendar_service.get_auth_url(force_fresh=True),
                "note": "You can use the fresh_auth_url to re-authenticate if needed"
            }

        auth_url = calendar_service.get_auth_url(force_fresh=True)
        return {
            "auth_url": auth_url,
            "message": "Fresh OAuth URL generated with cache-busting",
            "instructions": "Please visit the auth_url to authenticate. This URL includes cache-busting to prevent old URL issues."
        }
    except Exception as e:
        logger.error(f"Error generating fresh auth URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate fresh auth URL: {str(e)}")

# Calendar endpoints
@router.get("/calendars")
async def get_calendars():
    """Get all available calendars with theme information"""
    if not calendar_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Authentication required")

    calendars = await calendar_service.get_available_calendars()
    return {"calendars": calendars}

@router.post("/calendars/suggest")
async def suggest_calendar(data: dict):
    """Get calendar suggestions based on event data or query"""
    if not calendar_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Authentication required")

    event_data = data.get("event_data", {})
    query = data.get("query", "")

    suggestions = await calendar_service.suggest_calendar(event_data, query)
    return {"suggestions": suggestions}

# Root endpoint
@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CaliBOT - AI Calendar Bot is running",
        "version": __version__,
        "status": "operational"
    }
