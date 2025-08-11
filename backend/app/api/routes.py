from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.services.telegram import (
    TelegramBotService, 
    send_telegram_message, 
    answer_callback_query,
    edit_message_text
)
from app.services.ai_service import get_ai_response, get_small_talk_response
from app.services.google_calendar import GoogleCalendarService
from app.services.multi_event_operations import MultiEventOperationHandler
from app.services.event_queue_handler import EventQueueHandler
from app.api.models import TelegramUpdate
from app.services.conversation import conversation_state
from app.agent.calendar_agent import CalendarAgent
from app.services.telegram import create_confirmation_keyboard
from app.utils.message_formatter import MessageFormatter
from app.agent.nlp_agent import NLPAgent
from app.utils.message_formatter import MessageFormatter
from app.api.handlers import (
    query_and_filter_events,
    find_duplicates,
    process_batch_creation,
    create_single_event,
    IntentDispatcher,
    process_update_delete_with_confirmation,
)

# Import new centralized formatters for consistency
try:
    from app.utils.message_formatter import MessageFormatter
    from app.utils.inline_keyboard import InlineKeyboardHelper
except ImportError:
    # Fallback for development/testing
    MessageFormatter = None
    InlineKeyboardHelper = None
from datetime import datetime

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

## ui_helpers deprecated: all event formatting now uses MessageFormatter exclusively


async def check_for_duplicate_events(chat_id, events_to_create, calendar_service):
    """Check for potential duplicate events and ask user for confirmation"""
    duplicates_found = []
    
    for i, event in enumerate(events_to_create):
        if not isinstance(event, dict):
            continue
            
        # Query for existing events with same name on same date
        event_name = event.get("event_name", "")
        date = event.get("date", "")
        
        if not event_name or not date:
            logger.warning(f"Skipping duplicate check for incomplete event: {event}")
            continue
            
        query_params = {
            "event_name": event_name,
            "date": date
        }
        
        try:
            logger.info(f"Checking for duplicates of '{event_name}' on {date}")
            existing_events = await calendar_service.query_events(query_params)
            logger.info(f"Query result: {existing_events}")
            
            if existing_events.get("success") and existing_events.get("events"):
                # Check for events with similar names and overlapping times
                event_start = event.get("start_time", "")
                event_end = event.get("end_time", "")
                
                for existing in existing_events["events"]:
                    existing_summary = existing.get("summary", "").lower()
                    event_name_lower = event_name.lower()
                    
                    # Check if names are similar (exact match or contain each other)
                    if (existing_summary == event_name_lower or 
                        event_name_lower in existing_summary or 
                        existing_summary in event_name_lower):
                        
                        # Check time overlap for stronger duplicate detection
                        existing_start = existing.get("start", "")
                        if event_start and existing_start:
                            # Extract time from datetime string for comparison
                            try:
                                if event_start in existing_start:
                                    logger.info(f"Found potential duplicate: {existing_summary} at {existing_start}")
                                    duplicates_found.append({
                                        "new_event": event,
                                        "existing_event": existing,
                                        "index": i
                                    })
                                    break  # Only flag one duplicate per new event
                            except Exception as e:
                                logger.warning(f"Error comparing times: {e}")
        except Exception as e:
            logger.warning(f"Error checking for duplicates: {e}")
    
    logger.info(f"Found {len(duplicates_found)} potential duplicates")
    return duplicates_found


# Initialize services
router = APIRouter()
telegram_service = TelegramBotService()
calendar_service = GoogleCalendarService()
calendar_agent = CalendarAgent()
multi_event_handler = MultiEventOperationHandler(calendar_service, telegram_service, conversation_state)
event_queue_handler = EventQueueHandler(telegram_service, conversation_state, calendar_service, calendar_agent)
ai_agent = NLPAgent()

access_token = None



@router.post("/webhook")
async def telegram_webhook(update: TelegramUpdate):
    """Handle incoming Telegram messages and callback queries"""
    
    logger.info(f"📨 Received Telegram update: {update}")
    
    # Handle callback queries (inline keyboard button presses)
    if hasattr(update, 'callback_query') and update.callback_query:
        return await handle_callback_query(update.callback_query)
    
    # Handle regular messages
    if not update.message:
        return {"status": "ok"}
    
    chat_id = update.message["chat"]["id"]
    user_message = None
    message_type = "text"
    
    # Handle different message types
    if "text" in update.message:
        user_message = update.message["text"]
    
    logger.info(f"👤 User message from chat {chat_id}: '{user_message}'")
    
    if not user_message:
        await send_telegram_message(
            chat_id,
            "I'm sorry, I didn't understand that. Can you please rephrase your message?"
        )
        return {"status": "ok"}
    
    # Process the message through the main logic
    return await process_user_message(chat_id, user_message, message_type)

async def handle_callback_query(callback_query):
    """Handle inline keyboard button presses"""
    chat_id = callback_query["message"]["chat"]["id"]
    message_id = callback_query["message"]["message_id"]
    callback_data = callback_query["data"]
    callback_query_id = callback_query["id"]
    
    logger.info(f"🔘 Callback query from chat {chat_id}: {callback_data}")
    
    # Answer the callback query to remove loading indicator
    await answer_callback_query(callback_query_id, "Processing...")
    
    # Handle different callback types
    if callback_data == "confirm_yes":
        return await handle_confirmation_callback(chat_id, message_id, "yes")
    elif callback_data == "confirm_no":
        return await handle_confirmation_callback(chat_id, message_id, "no")
    elif callback_data == "confirm_all" or callback_data.startswith("confirm_all_"):
        return await handle_confirmation_callback(chat_id, message_id, "all")
    elif callback_data == "confirm_one" or callback_data.startswith("confirm_one_"):
        return await handle_confirmation_callback(chat_id, message_id, "one")
    elif callback_data.startswith("confirm_") and not callback_data.startswith("confirm_all"):
        # Handle single event confirmation (e.g., "confirm_update this event")
        return await handle_confirmation_callback(chat_id, message_id, "yes")
    elif callback_data == "confirm_cancel" or callback_data.startswith("cancel_"):
        return await handle_confirmation_callback(chat_id, message_id, "cancel")
    elif callback_data.startswith("select_event_"):
        event_index = int(callback_data.split("_")[-1])
        return await handle_event_selection(chat_id, message_id, event_index)
    elif callback_data == "select_all":
        return await handle_event_selection(chat_id, message_id, "all")
    elif callback_data == "select_cancel":
        return await handle_event_selection(chat_id, message_id, "cancel")
    else:
        logger.warning(f"Unknown callback data: {callback_data}")
        return {"status": "ok"}

async def handle_confirmation_callback(chat_id: int, message_id: int, confirmation: str):
    """Handle confirmation responses from inline keyboards"""
    # Update the conversation state with the user's choice
    conversation_state.add_message(chat_id, confirmation, "user")
    
    # Get the original confirmation message from conversation history
    recent_messages = conversation_state.get_recent_messages(chat_id, 3)
    original_confirmation_msg = None
    for msg in recent_messages:
        if (msg.get("role") == "assistant" and 
            "Are you sure you want to" in msg.get("content", "")):
            original_confirmation_msg = msg.get("content", "")
            break
    
    # Edit the message based on confirmation type and remove keyboard
    if confirmation == "yes":
        # Keep original message but add confirmation status and remove keyboard
        if original_confirmation_msg:
            # Avoid duplicating status line if already appended
            if "✅ **Confirmed**" in original_confirmation_msg:
                new_text = original_confirmation_msg
            else:
                new_text = f"{original_confirmation_msg}\n\n✅ **Confirmed** - Processing your request..."
            await edit_message_text(chat_id, message_id, new_text, reply_markup={})
        else:
            await edit_message_text(
                chat_id, 
                message_id, 
                "✅ **Confirmed** - Processing your request...",
                reply_markup={}
            )
    elif confirmation == "no":
        # Keep original message but add cancellation status and remove keyboard
        if original_confirmation_msg:
            if "❌ **Cancelled**" in original_confirmation_msg:
                new_text = original_confirmation_msg
            else:
                new_text = f"{original_confirmation_msg}\n\n❌ **Cancelled** - Request has been cancelled"
            await edit_message_text(chat_id, message_id, new_text, reply_markup={})
        else:
            await edit_message_text(
                chat_id, 
                message_id, 
                "❌ **Cancelled** - Request has been cancelled",
                reply_markup={}
            )
    elif confirmation in ["all", "one", "cancel"]:
        # CRITICAL FIX: Always remove keyboard from original message for all multi-event operations
        if original_confirmation_msg:
            if confirmation == "all":
                status_text = "✅ **Processing all events** - Please wait..."
            elif confirmation == "one":
                status_text = "✅ **Processing one by one** - See next message..."
            else:
                status_text = "❌ **Cancelled** - Operation cancelled"
            
            await edit_message_text(
                chat_id, 
                message_id, 
                f"{original_confirmation_msg}\n\n{status_text}",
                reply_markup={}
            )
        
        # Clear any pending operations if cancelled
        if confirmation == "cancel":
            multi_event_handler.clear_pending_operations(chat_id)
            event_queue_handler.clear_queue(chat_id)
            await send_telegram_message(chat_id, "❌ Operation cancelled")
            return {"status": "ok"}
    else:
        # Fallback - should rarely be used
        await edit_message_text(
            chat_id, 
            message_id, 
            f"Choice: {confirmation}"
        )
    
    # CRITICAL FIX: Handle pending operations directly instead of triggering new intent extraction
    if multi_event_handler.has_pending_operation(chat_id):
        logger.info(f"Processing pending multi-event operation with confirmation: {confirmation}")
        try:
            confirmation_result = await multi_event_handler.confirm_operation(chat_id, confirmation)
            if confirmation_result.get("requires_user_action"):
                # Send as new message if still requires action (like queue processing)
                keyboard = confirmation_result.get("keyboard")
                if keyboard:
                    await send_telegram_message(chat_id, confirmation_result["message"], reply_markup=keyboard)
                else:
                    await send_telegram_message(chat_id, confirmation_result["message"])
            else:
                # Send final result as new message
                await send_telegram_message(chat_id, confirmation_result["message"])
            
            conversation_state.add_message(chat_id, "assistant", confirmation_result["message"])
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Error processing pending operation: {e}")
            await send_telegram_message(chat_id, f"Error processing operation: {str(e)}")
            return {"status": "ok"}
    
    # Check event queue system
    if event_queue_handler.has_pending_queue(chat_id):
        logger.info(f"Processing pending event queue with confirmation: {confirmation}")
        try:
            queue_result = await event_queue_handler.process_queue_response(chat_id, confirmation)
            
            # CRITICAL FIX: Handle one-by-one processing properly
            if queue_result.get("queue_continues"):
                # Send the current result first
                await send_telegram_message(chat_id, queue_result["message"])
                conversation_state.add_message(chat_id, "assistant", queue_result["message"])
                
                # Then send the next confirmation as a separate message
                next_conf = queue_result.get("next_confirmation", {})
                if next_conf:
                    keyboard = next_conf.get("keyboard")
                    if keyboard:
                        await send_telegram_message(chat_id, next_conf["message"], reply_markup=keyboard)
                    else:
                        await send_telegram_message(chat_id, next_conf["message"])
                    conversation_state.add_message(chat_id, "assistant", next_conf["message"])
            else:
                # Standard processing for complete operations
                keyboard = queue_result.get("keyboard")
                if keyboard:
                    await send_telegram_message(chat_id, queue_result["message"], reply_markup=keyboard)
                else:
                    await send_telegram_message(chat_id, queue_result["message"])
                conversation_state.add_message(chat_id, "assistant", queue_result["message"])
            
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Error processing pending queue: {e}")
            await send_telegram_message(chat_id, f"Error processing queue: {str(e)}")
            return {"status": "ok"}
    
    # If no pending operations, fall back to regular processing
    return await process_user_message(chat_id, confirmation, "callback")

async def handle_event_selection(chat_id: int, message_id: int, selection):
    """Handle event selection from inline keyboards"""
    if selection == "cancel":
        await edit_message_text(chat_id, message_id, "❌ Selection cancelled")
        return {"status": "ok"}
    elif selection == "all":
        await edit_message_text(chat_id, message_id, "✅ All events selected")
        # Process as "all" confirmation
        return await process_user_message(chat_id, "all", "callback")
    else:
        # Handle individual event selection
        await edit_message_text(chat_id, message_id, f"✅ Selected event #{selection + 1}")
        # Store the selection and continue with individual processing
        conversation_state.set_data(chat_id, "selected_event_index", selection)
        return await process_user_message(chat_id, "one", "callback")

async def process_user_message(chat_id: int, user_message: str, message_type: str = "text"):
    """Process user message (from regular text or callback)"""
    
    try:
        auth_check = calendar_service.is_authenticated()
        logger.info(f"Auth check result: {auth_check}")

        
        if auth_check is not True:
            url_auth = calendar_service.get_auth_url()
            await send_telegram_message(
                chat_id,
                f"To use this bot, please authenticate your Google account: [Click here]({url_auth})"
            )
            return {"status": "ok"}
        
        # Determine if this appears to be a fresh command while a queue is active
        is_confirmation_word = user_message.lower().strip() in ["yes", "no", "all", "one", "cancel", "y", "n"]
        if not is_confirmation_word and event_queue_handler.has_pending_queue(chat_id):
            logger.info(f"New unrelated command detected while queue active; clearing queue for chat {chat_id}")
            event_queue_handler.clear_queue(chat_id)
            await send_telegram_message(chat_id, "Previous pending operation cancelled. Starting new request.")
        # Add user message to conversation history
        conversation_state.add_message(chat_id, "user", user_message, message_type)
        history = conversation_state.get_conversation_history(chat_id)
        
        # Check for pending duplicate creation confirmation
        recent_messages = conversation_state.get_recent_messages(chat_id, 5)
        has_pending_duplicates = any("PENDING_DUPLICATE_CREATION:" in msg.get("content", "") 
                                   for msg in recent_messages if msg.get("role") == "system")
        
        if has_pending_duplicates:
            logger.info(f"Processing duplicate creation confirmation: '{user_message}'")
            
            if is_confirmation_yes(user_message):
                # User confirmed to create duplicates - extract event count
                for msg in recent_messages:
                    if msg.get("role") == "system" and "PENDING_DUPLICATE_CREATION:" in msg.get("content", ""):
                        try:
                            event_count_str = msg["content"].split("PENDING_DUPLICATE_CREATION:")[1].split(" events")[0]
                            event_count = int(event_count_str)
                            
                            # Remove the pending flag
                            conversation_state.remove_system_message(chat_id, "PENDING_DUPLICATE_CREATION:")
                            
                            # The confirmation is already shown in the edited message, no need for additional message
                            return {"status": "ok"}
                        except Exception as e:
                            logger.error(f"Error processing duplicate confirmation: {e}")
                            break
            
            elif is_confirmation_no(user_message):
                # User declined to create duplicates
                conversation_state.remove_system_message(chat_id, "PENDING_DUPLICATE_CREATION:")
                # The cancellation is already shown in the edited message, no need for additional message
                return {"status": "ok"}
            
            else:
                # Invalid response to duplicate confirmation
                await send_telegram_message(chat_id, "Please respond with:\n• 'yes' to create duplicate events\n• 'no' or 'cancel' to cancel creation")
                conversation_state.add_message(chat_id, "assistant", "Please respond with:\n• 'yes' to create duplicate events\n• 'no' or 'cancel' to cancel creation")
                return {"status": "ok"}
        
        # Simple fast-path for common schedule queries to reduce LLM dependency & mitigate malformed '"intent"' failures
        def _simple_schedule_query(msg: str):
            m = msg.lower().strip()
            if len(m) < 3:
                return None
            import re
            today = datetime.now().date()
            weekday_map = {"monday":0, "tuesday":1, "wednesday":2, "thursday":3, "friday":4, "saturday":5, "sunday":6}
            date_iso = None
            iso_match = re.search(r"(20\d{2}-\d{2}-\d{2})", m)
            if iso_match:
                date_iso = iso_match.group(1)
            elif any(w in m for w in ["today", "todays", "this day"]):
                date_iso = today.strftime("%Y-%m-%d")
            elif "tomorrow" in m:
                from datetime import timedelta
                date_iso = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                for wd, idx in weekday_map.items():
                    if wd in m:
                        from datetime import timedelta
                        delta = (idx - today.weekday()) % 7
                        if "next" in m and delta == 0:
                            delta = 7
                        date_iso = (today + timedelta(days=delta)).strftime("%Y-%m-%d")
                        break
            schedule_keywords = [
                "what's on", "whats on", "what do i have", "show me", "show my", "my schedule", "any events", "what is on my calendar",
                "schedule", "events today", "events tomorrow", "do i have anything", "what do i have tomorrow", "what do i have today"
            ]
            if any(k in m for k in schedule_keywords) or re.fullmatch(r"(today|tomorrow)", m):
                return {"intent": "query", "date": date_iso or today.strftime("%Y-%m-%d"), "confirmation_needed": False}
            if m in ["today", "tomorrow"]:
                return {"intent": "query", "date": date_iso or today.strftime("%Y-%m-%d"), "confirmation_needed": False}
            return None

        event_data = None
        simple_query_event = _simple_schedule_query(user_message)
        if simple_query_event:
            event_data = simple_query_event
            logger.info(f"Simple schedule query shortcut applied: {event_data}")
        else:
            # logger.info(f"---------------------Conversation history: {history}")
            # Check relevancy before extracting intent
            relevancy_result = await ai_agent.check_relevancy(user_message, history)
            if not relevancy_result.get("relevant"):
                ai_response = await get_small_talk_response(user_message, history)
                await send_telegram_message(chat_id, ai_response)
                conversation_state.add_message(chat_id, "assistant", ai_response)
                return {"status": "ok"}  
            try:
                event_data = await ai_agent.extract_intent(user_message, history)
                logger.info(f"Extracted intent: {event_data}")
                if not isinstance(event_data, dict):
                    logger.error(f"CRITICAL: Invalid event_data type: {type(event_data)} - {event_data}")
                    await send_telegram_message(chat_id, "Sorry, I had trouble understanding your request. Could you please try again?")
                    conversation_state.add_message(chat_id, "assistant", "Sorry, I had trouble understanding your request. Could you please try again?")
                    return {"status": "ok"}
                # NEW DEFENSIVE GUARD: handle pathological string-only LLM response caught before downstream logic
                if list(event_data.keys()) == ['intent'] and not event_data.get('intent'):
                    logger.error("Pathological empty 'intent' key returned from LLM - applying fallback query intent")
                    event_data = {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            except Exception as e:
                logger.error(f"CRITICAL: Error in AI intent extraction: {e}")
                await send_telegram_message(chat_id, "I'm experiencing technical difficulties. Please try again in a moment.")
                conversation_state.add_message(chat_id, "assistant", "I'm experiencing technical difficulties. Please try again in a moment.")
                return {"status": "ok"}
        
        # Additional safety check for required fields
        if "intent" not in event_data:
            logger.error(f"CRITICAL: No 'intent' field in event_data: {event_data}")
            # Apply safe fallback to query intent instead of user-facing failure to mask transient LLM glitch
            event_data = {"intent": "query", "date": datetime.now().strftime("%Y-%m-%d"), "confirmation_needed": False}
            logger.info("Applied fallback query intent due to missing 'intent' key")

        # Handle batch creation format
        if event_data.get("intent") == "batch_create" and "events" in event_data:
            result = await process_batch_creation(
                chat_id,
                event_data,
                calendar_service,
                send_telegram_message,
                # format_event_for_display deprecated; using MessageFormatter directly
                format_duplicate_confirmation_with_keyboard,
                conversation_state,
                lambda enhanced: find_duplicates(enhanced, calendar_service),
            )
            if result.get("handled"):
                return result
        
        # Check if user has pending event queue (NEW: Priority check)
        if event_queue_handler.has_pending_queue(chat_id):
            logger.info(f"Processing event queue confirmation")
            
            queue_result = await event_queue_handler.process_queue_response(chat_id, user_message)
            
            # CRITICAL FIX: Handle one-by-one processing properly (same logic as callback handler)
            if queue_result.get("queue_continues"):
                # Send the current result first
                await send_telegram_message(chat_id, queue_result["message"])
                conversation_state.add_message(chat_id, "assistant", queue_result["message"])
                
                # Then send the next confirmation as a separate message
                next_conf = queue_result.get("next_confirmation", {})
                if next_conf:
                    keyboard = next_conf.get("keyboard")
                    if keyboard:
                        await send_telegram_message(chat_id, next_conf["message"], reply_markup=keyboard)
                    else:
                        await send_telegram_message(chat_id, next_conf["message"])
                    conversation_state.add_message(chat_id, "assistant", next_conf["message"])
            else:
                # Standard processing for complete operations
                keyboard = queue_result.get("keyboard")
                if keyboard:
                    await send_telegram_message(chat_id, queue_result["message"], reply_markup=keyboard)
                else:
                    await send_telegram_message(chat_id, queue_result["message"])
                conversation_state.add_message(chat_id, "assistant", queue_result["message"])
            
            return {"status": "ok"}

        # Check if this is a multi-event request that should be queued
        if event_queue_handler.detect_multi_event_request(event_data):
            logger.info(f"Detected multi-event request, creating queue")
            
            queue_result = event_queue_handler.create_event_queue(chat_id, event_data)
            keyboard = queue_result.get("keyboard")
            if keyboard:
                await send_telegram_message(chat_id, queue_result["message"], reply_markup=keyboard)
            else:
                await send_telegram_message(chat_id, queue_result["message"])
            conversation_state.add_message(chat_id, "assistant", queue_result["message"])
            
            return {"status": "ok"}

        # Handle multi-event operations (delete, update) with queue-based approach
        handled_update_delete = await process_update_delete_with_confirmation(
            chat_id,
            event_data,
            calendar_service,
            event_queue_handler,
            multi_event_handler,
            send_telegram_message,
            conversation_state,
        )
        if handled_update_delete.get("handled"):
            return handled_update_delete

        # Handle confirmation intent (user saying yes/confirm to something)
        if event_data["intent"] == "confirm":
            logger.info(f"User confirmation received")
            # Normalize confirmation text
            confirmation_text = user_message.strip().lower()
            if confirmation_text in ["yes", "y", "confirm", "ok", "proceed"]:
                # Check event queue system first
                if event_queue_handler.has_pending_queue(chat_id):
                    logger.info(f"Processing confirmation for pending event queue")
                    queue_result = await event_queue_handler.process_queue_response(chat_id, confirmation_text)
                    await send_telegram_message(chat_id, queue_result["message"])
                    conversation_state.add_message(chat_id, "assistant", queue_result["message"])
                # Check legacy multi-event handler
                elif multi_event_handler.has_pending_operation(chat_id):
                    logger.info(f"Processing confirmation for pending multi-event operation")
                    confirmation_result = await multi_event_handler.confirm_operation(chat_id, confirmation_text)
                    await send_telegram_message(chat_id, confirmation_result["message"])
                    conversation_state.add_message(chat_id, "assistant", confirmation_result["message"])
                else:
                    await send_telegram_message(chat_id, "I don't have any pending operations to confirm. What would you like me to do?")
                    conversation_state.add_message(chat_id, "assistant", "I don't have any pending operations to confirm. What would you like me to do?")
                return {"status": "ok"}
            else:
                await send_telegram_message(chat_id, "Sorry, I didn't understand your confirmation. Please reply with 'yes' to confirm.")
                conversation_state.add_message(chat_id, "assistant", "Sorry, I didn't understand your confirmation. Please reply with 'yes' to confirm.")
                return {"status": "ok"}

        # If no confirmation is needed, proceed with the action
        if event_data.get("confirmation_needed") is False:
            logger.info(f"Processing intent '{event_data.get('intent')}' without confirmation")
            
            if event_data["intent"] in ["create", "batch_create"]:
                # Detect batch creation scenarios (multiple events)
                events_to_create = []
                
                # Format 0: Direct batch_create from multiple JSON objects
                if event_data["intent"] == "batch_create" and 'events' in event_data:
                    events_to_create = event_data['events']
                    logger.info(f"Detected batch_create format with {len(events_to_create)} events from multiple JSON objects")
                
                # Format 1: 'events' array with individual event objects
                elif 'events' in event_data and isinstance(event_data['events'], list):
                    events_to_create = event_data['events']
                    logger.info(f"Detected events array format with {len(events_to_create)} events")
                
                # Format 2: Arrays in start_time/end_time fields
                elif (isinstance(event_data.get('start_time'), list) and 
                      isinstance(event_data.get('end_time'), list) and 
                      len(event_data.get('start_time', [])) == len(event_data.get('end_time', []))):
                    
                    start_times = event_data['start_time']
                    end_times = event_data['end_time']
                    events_to_create = []
                    
                    for start, end in zip(start_times, end_times):
                        events_to_create.append({
                            'start_time': start,
                            'end_time': end
                        })
                    logger.info(f"Detected array format, converted to {len(events_to_create)} events")
                
                # Format 3: Multiple times detected in description (fallback)
                elif event_data.get('description') and ('lessons' in event_data.get('description', '').lower()):
                    description = event_data.get('description', '')
                    import re
                    # Look for patterns like "at 8:00, 10:00, 11:00" or "for 8, 10, 11, 12"
                    time_patterns = re.findall(r'\b(\d{1,2}):?(\d{2})?\b', description)
                    if len(time_patterns) > 1:
                        events_to_create = []
                        for hour_match in time_patterns:
                            hour = int(hour_match[0])
                            if hour < 24:  # Valid hour
                                start_time = f"{hour:02d}:00"
                                end_time = f"{hour+1:02d}:00" if hour < 23 else "23:59"
                                events_to_create.append({
                                    'start_time': start_time,
                                    'end_time': end_time
                                })
                        if events_to_create:
                            logger.info(f"Detected {len(events_to_create)} events from description fallback")
                
                # Process batch creation
                if events_to_create:
                    logger.info(f"Processing batch creation of {len(events_to_create)} events")
                    
                    successful_events = []
                    failed_events = []
                    
                    for i, single_event_data in enumerate(events_to_create):
                        # Create individual event data by merging base data with specific event times
                        individual_event = event_data.copy()
                        individual_event.update(single_event_data)
                        
                        # Remove batch-specific keys to avoid conflicts
                        keys_to_remove = ['events', 'start_time', 'end_time']
                        for key in keys_to_remove:
                            if key in individual_event and key not in single_event_data:
                                del individual_event[key]
                        
                        # Add the specific times back
                        individual_event['start_time'] = single_event_data.get('start_time')
                        individual_event['end_time'] = single_event_data.get('end_time')
                        
                        logger.info(f"Creating event {i+1}/{len(events_to_create)}: {individual_event}")
                        
                        try:
                            calendar_response = await calendar_service.create_event(individual_event)
                            if calendar_response["success"]:
                                successful_events.append({
                                    'time': f"{individual_event.get('start_time', 'Unknown')}-{individual_event.get('end_time', 'Unknown')}",
                                    'link': calendar_response['event_link'],
                                    'calendar': calendar_response.get('calendar_used', 'primary')
                                })
                            else:
                                failed_events.append({
                                    'time': f"{individual_event.get('start_time', 'Unknown')}-{individual_event.get('end_time', 'Unknown')}",
                                    'error': calendar_response.get('message', 'Unknown error')
                                })
                        except Exception as e:
                            logger.error(f"Failed to create event {i+1}: {e}")
                            failed_events.append({
                                'time': f"{individual_event.get('start_time', 'Unknown')}-{individual_event.get('end_time', 'Unknown')}",
                                'error': str(e)
                            })
                    
                    # Send comprehensive response
                    if successful_events:
                        calendar_name = successful_events[0]['calendar']
                        if len(successful_events) == 1:
                            success_msg = f"Event created successfully:\n\n"
                        else:
                            success_msg = f"Successfully created {len(successful_events)} events:\n\n"
                        
                        for i, event in enumerate(successful_events):
                            # Create proper event data structure for formatting
                            event_for_formatting = {
                                'event_name': event_data.get('event_name', 'Event'),
                                'start_time': event['time'].split('-')[0] if '-' in event['time'] else event['time'],
                                'end_time': event['time'].split('-')[1] if '-' in event['time'] else event['time'],
                                'date': event_data.get('date', 'today'),
                                'calendar_name': event['calendar']
                            }
                            calendar_result = {"success": True, "event_link": event['link']}
                            formatted_event = MessageFormatter.format_single_event_display({
                                'summary': event_for_formatting.get('event_name') or event_for_formatting.get('summary'),
                                'start': event_for_formatting.get('start_time') or event_for_formatting.get('start'),
                                'end': event_for_formatting.get('end_time') or event_for_formatting.get('end'),
                                'calendar_name': calendar_result.get('calendar_used') or event_for_formatting.get('calendar_name'),
                                'id': calendar_result.get('event_id'),
                                'htmlLink': calendar_result.get('event_link')
                            })
                            success_msg += f"{formatted_event}\n"
                        
                        if failed_events:
                            success_msg += f"\nFailed to create {len(failed_events)} events:\n"
                            for event in failed_events:
                                success_msg += f"• {event['time']}: {event['error']}\n"
                        
                        await send_telegram_message(chat_id, success_msg)
                    else:
                        failure_msg = f"Failed to create all {len(failed_events)} events:\n"
                        for event in failed_events:
                            failure_msg += f"• {event['time']}: {event['error']}\n"
                        await send_telegram_message(chat_id, failure_msg)
                
                else:
                    # Single event creation (refactored call)
                    await create_single_event(
                        chat_id,
                        event_data,
                        calendar_service,
                        send_telegram_message,
                        # deprecated format_event_for_display removed
                        conversation_state,
                    )
                    return {"status": "ok"}

            elif event_data["intent"] in ["update", "delete"]:
                # Check if user is referring to recent events with pronouns
                user_message_lower = user_message.lower()
                is_pronoun_reference = any(word in user_message_lower for word in 
                    ["these", "those", "this", "that", "them", "it"])
                
                if is_pronoun_reference and not event_data.get("event_name"):
                    # Look for recently created/mentioned events in conversation history
                    recent_messages = conversation_state.get_recent_messages(chat_id, 5)
                    recent_event_names = []
                    
                    for msg in reversed(recent_messages):
                        if msg.get("role") == "assistant" and "successfully created" in msg.get("content", "").lower():
                            # Extract event names from recent creation confirmations
                            content = msg["content"]
                            import re
                            # Look for pattern like "Lesson (" to extract event names
                            matches = re.findall(r'([A-Z][a-zA-Z\s]+)\s*\(', content)
                            if matches:
                                # Use the most recent event name found
                                event_data["event_name"] = matches[0].strip().lower()
                                logger.info(f"Resolved pronoun reference to recent event: {event_data['event_name']}")
                                break
                    
                    # If still no event name found, get today's events as fallback
                    if not event_data.get("event_name"):
                        from datetime import datetime
                        today = datetime.now().strftime("%Y-%m-%d")
                        event_data["date"] = today
                
                # Query events based on event details
                matched_events = await calendar_service.query_events({
                    "event_name": event_data.get("event_name", ""),
                    "date": event_data.get("date", "")
                })

                if not matched_events["success"] or not matched_events["events"]:
                    response = "No events found matching your criteria."
                    await send_telegram_message(chat_id, response)
                    conversation_state.add_message(chat_id, "assistant", response)
                    return {"status": "ok"}

                events = matched_events["events"]
                logger.info(f"================> Matched events: {events}")
                
                # If multiple events, use inline keyboard for confirmation
                if len(events) > 1:
                    action = event_data["intent"]
                    # Build confirmation using MessageFormatter for multi-event create/update/delete
                    confirmation_msg = MessageFormatter.format_confirmation_message(action, [
                        {
                            'summary': e.get('summary') or e.get('event_name'),
                            'start': e.get('start') or e.get('start_time'),
                            'end': e.get('end') or e.get('end_time'),
                            'calendar_name': e.get('calendar_name'),
                            'id': e.get('id') or e.get('event_id'),
                            'htmlLink': e.get('htmlLink') or e.get('calendar_link')
                        } for e in events
                    ])
                    keyboard = create_confirmation_keyboard("multi_event")
                    
                    await send_telegram_message(chat_id, confirmation_msg, reply_markup=keyboard)
                    conversation_state.add_message(chat_id, "assistant", confirmation_msg)
                    
                    # Store pending operation for confirmation handling
                    multi_event_handler.store_pending_operation(chat_id, {
                        "type": f"{action}_multiple",
                        "events": events,
                        "original_request": event_data
                    })
                    
                    return {"status": "ok"}
                
                # Single event processing
                event_id = events[0]["id"]
                
                # Proceed with update or delete after getting event_id
                if event_data["intent"] == "update":
                    # Get the source calendar ID from the matched event
                    source_calendar_id = events[0].get('calendar_id', 'primary')
                    calendar_response = calendar_service.update_event(event_id, event_data, source_calendar_id)
                    if calendar_response["success"]:
                        updated_event = calendar_response.get('updated_event') or {}
                        formatted_event = MessageFormatter.format_single_event_display(updated_event, include_hyperlink=True)
                        change_note = "(moved)" if calendar_response.get("moved") else ""
                        success_msg = f"Successfully updated event {change_note}:\n\n{formatted_event}".strip()
                        await send_telegram_message(chat_id, success_msg)
                        conversation_state.add_message(chat_id, "assistant", success_msg)
                    else:
                        error_msg = f"Failed to update event: {calendar_response.get('message', 'Unknown error')}"
                        await send_telegram_message(chat_id, error_msg)
                        conversation_state.add_message(chat_id, "assistant", error_msg)
                elif event_data["intent"] == "delete":
                    # Get the source calendar ID from the matched event
                    source_calendar_id = events[0].get('calendar_id', 'primary')
                    calendar_response = calendar_service.delete_event(event_id, source_calendar_id)
                    if calendar_response["success"]:
                        event_name = MessageFormatter.format_event_title(events[0].get('summary', 'Event'))
                        success_msg = f"Successfully deleted: {event_name}"
                        await send_telegram_message(chat_id, success_msg)
                        conversation_state.add_message(chat_id, success_msg)
                        logger.info(f"DELETE{calendar_response}")
                    else:
                        error_msg = f"Failed to delete event: {calendar_response.get('message', 'Unknown error')}"
                        await send_telegram_message(chat_id, error_msg)
                        conversation_state.add_message(chat_id, error_msg)
                # Removed invalid ai_response reference (no AI response generated in this path)
                return {"status": "ok"}

        elif event_data["intent"] == "query":
            # Unified query handling using MessageFormatter only (Issue 4 formatting compliance)
            matched_events = await calendar_service.query_events({
                "event_name": event_data.get("event_name", ""),
                "date": event_data.get("date", "")
            })
            if not matched_events.get("success") or not matched_events.get("events"):
                await send_telegram_message(chat_id, "No matching events found.")
                return {"status": "ok"}
            events = matched_events["events"]
            logger.info(f"Found {len(events)} events with calendar info")
            for ev in events:
                logger.info(f"  • {ev.get('summary','No Title')} ({ev.get('calendar_name','Unknown')})")
            from app.utils.message_formatter import MessageFormatter
            if len(events) == 1:
                formatted_event = MessageFormatter.format_single_event_display(events[0], include_hyperlink=True)
                response = f"Found 1 event:\n\n{formatted_event}"
            else:
                title = f"Found {len(events)} events:"  # Consistent title format
                formatted_events = MessageFormatter.format_event_list_display(events, numbered=False, include_hyperlink=True)
                response = f"{title}\n\n{formatted_events}"
            await send_telegram_message(chat_id, response)
            conversation_state.add_message(chat_id, "assistant", response)
            return {"status": "ok"}

        elif event_data["intent"] == "calendar_management":
            logger.info(f"Calendar management request: {event_data}")
            calendar_action = event_data.get("calendar_action", "")
            
            if calendar_action == "create_calendar":
                calendar_name = event_data.get("calendar_name", "")
                response = f"I understand you want to create a new calendar called '{calendar_name}'. Unfortunately, I cannot create new calendars programmatically through the Google Calendar API. You'll need to:\n\n1. Go to calendar.google.com\n2. Click the '+' next to 'Other calendars'\n3. Choose 'Create new calendar'\n4. Enter '{calendar_name}' as the calendar name\n\nOnce created, I'll be able to help you add events to it!"
                await send_telegram_message(chat_id, response)
                conversation_state.add_message(chat_id, "assistant", response)
                return {"status": "ok"}
            
            elif calendar_action == "list_calendars":
                # Ensure calendars are loaded first
                await calendar_service.ensure_calendars_loaded()
                
                # Get list of available calendars
                calendars = calendar_service.calendar_agent.calendar_cache
                if calendars:
                    calendar_list = "\n".join([f"• {info['name']}" for info in calendars.values()])
                    response = f"Here are your available calendars:\n\n{calendar_list}"
                else:
                    response = "No calendars found. Please ensure you're authenticated with Google Calendar."
                
                logger.info(f"Sending calendar list: {response}")
                await send_telegram_message(chat_id, response)
                conversation_state.add_message(chat_id, "assistant", response)
                return {"status": "ok"}
            
            else:
                response = "I can help you list your calendars or provide guidance on creating new ones. What would you like to do?"
                await send_telegram_message(chat_id, response)
                conversation_state.add_message(chat_id, "assistant", response)
                return {"status": "ok"}

        # In case confirmation is needed (handling as needed)
        logger.info(f"Confirmation needed for intent: {event_data}")
        
        # For specific intents that need confirmation, use buttons instead of AI response
        intent = event_data.get("intent", "")
        
        if intent == "create" and event_data.get("confirmation_needed"):
            # Missing information for event creation - ask for details with buttons if appropriate
            missing_fields = []
            if not event_data.get("start_time"):
                missing_fields.append("start time")
            if not event_data.get("end_time"):
                missing_fields.append("end time")
            
            if missing_fields:
                response = f"I need more information to create your event:\n\n"
                response += f"• Event: {event_data.get('event_name', 'New Event')}\n"
                response += f"• Date: {event_data.get('date', 'today')}\n"
                response += f"• Missing: {', '.join(missing_fields)}\n\n"
                response += f"Please provide the missing information."
                
                await send_telegram_message(chat_id, response)
                conversation_state.add_message(chat_id, "assistant", response)
                return {"status": "ok"}
        
        elif intent in ["delete", "update"] and event_data.get("confirmation_needed"):
            # Use confirmation buttons for destructive operations
            action_text = "delete" if intent == "delete" else "update"
            target = event_data.get("event_name", "the event")
            
            confirmation_msg = f"Are you sure you want to {action_text} '{target}'?"
            keyboard = create_confirmation_keyboard("single_event")
            
            await send_telegram_message(chat_id, confirmation_msg, reply_markup=keyboard)
            conversation_state.add_message(chat_id, "assistant", confirmation_msg)
            return {"status": "ok"}
        
        # Fallback to AI response for non-query, non-confirmation intents needing conversational guidance
        if intent not in ["query"]:
            ai_response = await get_ai_response(event_data, history)
            logger.info(f"Bot response: '{ai_response}'")
            conversation_state.add_message(chat_id, "assistant", ai_response)
            await send_telegram_message(chat_id, ai_response)
            return {"status": "ok"}
        # Query already fully handled above; no extra AI filler message
        return {"status": "ok"}
            
    except HTTPException as he:
        # Handle authentication errors specifically
        if he.status_code == 401:
            url_auth = calendar_service.get_auth_url()
            await send_telegram_message(
                chat_id,
                f"Your Google authentication has expired. Please re-authenticate: [Click here]({url_auth})"
            )
            return {"status": "ok"}
        else:
            # Re-raise other HTTP exceptions
            raise he
    except Exception as e:
        await send_telegram_message(
            chat_id,
            "I apologize, but I'm having trouble processing your message right now. Please try again later."
        )
        logger.error(f"======>Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    


@router.get("/oauth2callback")
async def oauth_callback(request: Request):
    """Handle Google OAuth callback."""
    logger.info(f"Received OAuth callback with code: {request.query_params.get('code')}")
    return await calendar_service.handle_oauth_callback(request)


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

# Backward compatibility alias expected by older tests
async def process_webhook(chat_id: int, user_message: str):
    """Compatibility wrapper mapping old test import to current processing function."""
    return await process_user_message(chat_id, user_message, "text")
