from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.services.telegram import TelegramBotService, send_telegram_message
from app.services.ai_service import get_ai_response, get_small_talk_response
from app.services.google_calendar import GoogleCalendarService
from app.services.multi_event_operations import MultiEventOperationHandler
from app.services.event_queue_handler import EventQueueHandler
from app.api.models import TelegramUpdate
from app.services.conversation import conversation_state
from app.agent.nlp_agent import NLPAgent
from app.agent.calendar_agent import CalendarAgent

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()
telegram_service = TelegramBotService()
calendar_service = GoogleCalendarService()
calendar_agent = CalendarAgent()
nlp_agent = NLPAgent()
multi_event_handler = MultiEventOperationHandler(calendar_service, telegram_service, conversation_state)
event_queue_handler = EventQueueHandler(telegram_service, conversation_state, calendar_service, calendar_agent)

access_token = None


@router.post("/webhook")
async def telegram_webhook(update: TelegramUpdate):
    """Handle incoming Telegram messages"""
    
    logger.info(f"📨 Received Telegram update: {update}")
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
        
        # Add user message to conversation history
        conversation_state.add_message(chat_id, "user", user_message, message_type)
        history = conversation_state.get_conversation_history(chat_id)
        
        # logger.info(f"---------------------Conversation history: {history}")
        
        # Check relevancy before extracting intent
        relevancy_result = await nlp_agent.check_relevancy(user_message, history)
        # logger.info(f"------------------>RELEVANCY:{relevancy_result}")
        if not relevancy_result["relevant"]:
            ai_response = await get_small_talk_response(user_message, history)
            await send_telegram_message(chat_id, ai_response)
            conversation_state.add_message(chat_id, "assistant", ai_response)
            return {"status": "ok"}  
        
        
        event_data = await nlp_agent.extract_intent(user_message, history)
        logger.info(f"Extracted intent: {event_data}")

        # Check if user has pending event queue (NEW: Priority check)
        if event_queue_handler.has_pending_queue(chat_id):
            logger.info(f"Processing event queue confirmation")
            
            queue_result = await event_queue_handler.process_queue_response(chat_id, user_message)
            await send_telegram_message(chat_id, queue_result["message"])
            conversation_state.add_message(chat_id, "assistant", queue_result["message"])
            
            return {"status": "ok"}

        # Check if this is a multi-event request that should be queued
        if event_queue_handler.detect_multi_event_request(event_data):
            logger.info(f"Detected multi-event request, creating queue")
            
            queue_result = event_queue_handler.create_event_queue(chat_id, event_data)
            await send_telegram_message(chat_id, queue_result["message"])
            conversation_state.add_message(chat_id, "assistant", queue_result["message"])
            
            return {"status": "ok"}

        # Check if this is a confirmation for a pending multi-event operation (LEGACY)
        if multi_event_handler.has_pending_operation(chat_id):
            logger.info(f"Processing confirmation for pending multi-event operation")
            
            confirmation_result = await multi_event_handler.confirm_operation(chat_id, user_message)
            
            if confirmation_result["success"] or not confirmation_result["requires_user_action"]:
                await send_telegram_message(chat_id, confirmation_result["message"])
                conversation_state.add_message(chat_id, "assistant", confirmation_result["message"])
            else:
                # Still waiting for proper confirmation
                await send_telegram_message(chat_id, confirmation_result["message"])
                conversation_state.add_message(chat_id, "assistant", confirmation_result["message"])
            
            return {"status": "ok"}

        # Handle multi-event operations (delete, update) with queue-based approach
        if event_data["intent"] in ["delete", "update"] and not event_data.get("confirmation_needed", True):
            logger.info(f"Processing multi-event operation: {event_data['intent']}")
            
            # First, find matching events
            matched_events = await calendar_service.query_events({
                "event_name": event_data.get("event_name", ""),
                "date": event_data.get("date", "")
            })
            
            if not matched_events["success"] or not matched_events["events"]:
                await send_telegram_message(chat_id, f"No matching events found for {event_data['intent']} operation.")
                conversation_state.add_message(chat_id, "assistant", f"No matching events found for {event_data['intent']} operation.")
                return {"status": "ok"}
            
            events = matched_events["events"]
            
            # Validate events is a list
            if not isinstance(events, list):
                logger.error(f"Expected events to be a list, got {type(events)}: {events}")
                await send_telegram_message(chat_id, "Sorry, there was an error retrieving event data. Please try again.")
                conversation_state.add_message(chat_id, "assistant", "Sorry, there was an error retrieving event data. Please try again.")
                return {"status": "ok"}
            
            # Filter events to only include those matching the event name (if specified)
            if event_data.get("event_name"):
                filtered_events = []
                search_name = event_data["event_name"].lower()
                for event in events:
                    # Skip non-dictionary events during filtering
                    if not isinstance(event, dict):
                        logger.warning(f"Skipping non-dictionary event during filtering: {type(event)} - {event}")
                        continue
                    
                    if search_name in event.get("summary", "").lower():
                        filtered_events.append(event)
                events = filtered_events
            
            if not events:
                await send_telegram_message(chat_id, f"No events matching '{event_data.get('event_name', '')}' found.")
                conversation_state.add_message(chat_id, "assistant", f"No events matching '{event_data.get('event_name', '')}' found.")
                return {"status": "ok"}
            
            logger.info(f"Found {len(events)} matching events for {event_data['intent']} operation")
            
            # If multiple events, use queue system for individual confirmation
            if len(events) > 1:
                # Convert events to queue format
                queue_events = []
                for event in events:
                    # Ensure event is a dictionary before accessing its attributes
                    if not isinstance(event, dict):
                        logger.warning(f"Skipping non-dictionary event: {type(event)} - {event}")
                        continue
                    
                    # Validate required fields
                    if "id" not in event:
                        logger.warning(f"Skipping event without ID: {event}")
                        continue
                    
                    queue_event = {
                        "intent": event_data["intent"],
                        "event_id": event["id"],
                        "event_name": event.get("summary", "Untitled"),
                        "start_time": event.get("start", "Unknown time"),
                        "end_time": event.get("end", "Unknown time"),
                        "calendar_id": event.get("calendar_id", "primary"),
                        "calendar_name": event.get("calendar_name", "Default")
                    }
                    queue_events.append(queue_event)
                
                # Check if we have any valid events after filtering
                if not queue_events:
                    await send_telegram_message(chat_id, "Sorry, no valid events found that match your criteria.")
                    conversation_state.add_message(chat_id, "assistant", "Sorry, no valid events found that match your criteria.")
                    return {"status": "ok"}
                
                # Create queue
                queue_result = event_queue_handler.create_event_queue(chat_id, queue_events)
                await send_telegram_message(chat_id, queue_result["message"])
                conversation_state.add_message(chat_id, "assistant", queue_result["message"])
                return {"status": "ok"}
            
            # Single event - proceed directly (but still ask for confirmation)
            event = events[0]
            
            # Validate single event is a dictionary
            if not isinstance(event, dict):
                logger.error(f"Single event is not a dictionary: {type(event)} - {event}")
                await send_telegram_message(chat_id, "Sorry, there was an error processing the event data. Please try again.")
                conversation_state.add_message(chat_id, "assistant", "Sorry, there was an error processing the event data. Please try again.")
                return {"status": "ok"}
            
            # Validate required fields
            if "id" not in event:
                logger.error(f"Single event missing ID: {event}")
                await send_telegram_message(chat_id, "Sorry, the event data is incomplete. Please try again.")
                conversation_state.add_message(chat_id, "assistant", "Sorry, the event data is incomplete. Please try again.")
                return {"status": "ok"}
            
            event_summary = f"'{event.get('summary', 'Untitled')}' on {event.get('start', 'unknown date')}"
            
            if event_data["intent"] == "delete":
                confirmation_msg = f"Are you sure you want to delete {event_summary}? (yes/no)"
            else:  # update
                confirmation_msg = f"Are you sure you want to update {event_summary}? (yes/no)"
            
            # Store pending operation
            multi_event_handler.store_pending_operation(chat_id, {
                "intent": event_data["intent"],
                "events": [event],
                "original_data": event_data
            })
            
            await send_telegram_message(chat_id, confirmation_msg)
            conversation_state.add_message(chat_id, "assistant", confirmation_msg)
            return {"status": "ok"}

        # Handle confirmation intent (user saying yes/confirm to something)
        if event_data["intent"] == "confirm":
            logger.info(f"User confirmation received")
            
            # Check if there's a pending event queue first (NEW SYSTEM)
            if event_queue_handler.has_pending_queue(chat_id):
                logger.info(f"Processing confirmation for pending event queue")
                queue_result = await event_queue_handler.process_queue_response(chat_id, "yes")
                await send_telegram_message(chat_id, queue_result["message"])
                conversation_state.add_message(chat_id, "assistant", queue_result["message"])
            # Check if there's a pending operation (LEGACY SYSTEM)
            elif multi_event_handler.has_pending_operation(chat_id):
                logger.info(f"Processing confirmation for pending multi-event operation")
                confirmation_result = await multi_event_handler.confirm_operation(chat_id, "yes")
                await send_telegram_message(chat_id, confirmation_result["message"])
                conversation_state.add_message(chat_id, "assistant", confirmation_result["message"])
            else:
                await send_telegram_message(chat_id, "I don't have any pending operations to confirm. What would you like me to do?")
                conversation_state.add_message(chat_id, "assistant", "I don't have any pending operations to confirm. What would you like me to do?")
            
            return {"status": "ok"}

        # If no confirmation is needed, proceed with the action
        if event_data["confirmation_needed"] is False:
            logger.info(f"Processing intent '{event_data['intent']}' without confirmation")
            
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
                        success_msg = f"Successfully created {len(successful_events)} events in your '{calendar_name}' calendar:\n"
                        for event in successful_events:
                            success_msg += f"• {event['time']}\n"
                        
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
                    # Single event creation (existing logic)
                    calendar_response = await calendar_service.create_event(event_data)
                    if calendar_response["success"]:
                        calendar_info = f" in your '{calendar_response.get('calendar_used', 'primary')}' calendar" if calendar_response.get('calendar_used') else ""
                        await send_telegram_message(
                            chat_id, f"Event created successfully{calendar_info}! Here's the link to your event: {calendar_response['event_link']}"
                        )
                
                return {"status": "ok"}

            elif event_data["intent"] in ["update", "delete"]:
                # Query events based on event details (using the same query for both update and delete)
                matched_events = await calendar_service.query_events({
                    "event_name": event_data.get("event_name", ""),
                    "date": event_data.get("date", "")
                })

                if not matched_events["success"] or not matched_events["events"]:
                    response = "No matching events found."
                    await send_telegram_message(chat_id, response)
                    conversation_state.add_message(chat_id, "assistant", response)
                    return {"status": "ok"}

                events = matched_events["events"]
                logger.info(f"================> Matched events: {events}")
                event_id = None
                # if len(events) == 1:
                #     event_id = events[0]["id"]
                #     ai_response = await get_ai_response(event_data, history)
                #     await send_telegram_message(chat_id, ai_response)
                # else:
                event_list = "\n".join(
                    [f"{idx + 1}. {event['summary']} - {event['start']}" for idx, event in enumerate(events)]
                )
                event_id = events[0]["id"]
                ai_response = await get_ai_response(event_data, history)
                await send_telegram_message(chat_id, ai_response)

                # Proceed with update or delete after getting event_id
                if event_id:
                    if event_data["intent"] == "update":
                        # Get the source calendar ID from the matched event
                        source_calendar_id = events[0].get('calendar_id', 'primary')
                        calendar_response = calendar_service.update_event(event_id, event_data, source_calendar_id)
                        if calendar_response["success"]:
                            if calendar_response.get("moved"):
                                await send_telegram_message(
                                    chat_id, f"Event moved successfully to {calendar_response.get('to_calendar')}! Here's the link: {calendar_response['event_link']}"
                                )
                            else:
                                await send_telegram_message(
                                    chat_id, f"Event updated successfully! Here's the link to your event: {calendar_response['event_link']}"
                                )
                    elif event_data["intent"] == "delete":
                        # Get the source calendar ID from the matched event
                        source_calendar_id = events[0].get('calendar_id', 'primary')
                        calendar_response = calendar_service.delete_event(event_id, source_calendar_id)
                        logger.info(f"DELETE{calendar_response}")
                        if calendar_response["success"]:
                            await send_telegram_message(chat_id, f"Event deleted successfully! ({len(events)} event{'s' if len(events) != 1 else ''} found)")
                        else:
                            await send_telegram_message(chat_id, f"Failed to delete event: {calendar_response.get('message', 'Unknown error')}")
                # Add AI response to conversation history
                conversation_state.add_message(chat_id, "assistant", ai_response)
                return {"status": "ok"}

            elif event_data["intent"] == "query":
                # Query events in Google Calendar based on the event details
                matched_events = await calendar_service.query_events({
                    "event_name": event_data.get("event_name", ""),
                    "date": event_data.get("date", "")
                })

                if not matched_events["success"] or not matched_events["events"]:
                    await send_telegram_message(chat_id, "No matching events found.")
                    return {"status": "ok"}

                events = matched_events["events"]
                logger.info(f"Found {len(events)} events with calendar info")
                for event in events:
                    logger.info(f"  • {event.get('summary', 'No Title')} in calendar '{event.get('calendar_name', 'Unknown')}'")

                if len(events) == 1:
                    event_id = events[0]["id"]
                    ai_response = await get_ai_response(events[0], history)
                    await send_telegram_message(chat_id, ai_response)
                else:
                    # Include calendar names in the event list
                    event_list = "\n".join([
                        f"{idx + 1}. {event['summary']} - {event['start']} (Calendar: {event.get('calendar_name', 'Unknown')})" 
                        for idx, event in enumerate(events)
                    ])
                    ai_response = await get_ai_response({"events": event_list, "action": "list_events"}, history)
                    await send_telegram_message(chat_id, ai_response)
                # Add AI response to conversation history
                conversation_state.add_message(chat_id, "assistant", ai_response)
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
        ai_response = await get_ai_response(event_data, history)
        logger.info(f"Bot response: '{ai_response}'")
        # Add AI response to conversation history
        conversation_state.add_message(chat_id, "assistant", ai_response)
        await send_telegram_message(chat_id, ai_response)
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
