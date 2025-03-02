from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.services.telegram import TelegramBotService, send_telegram_message
from app.services.ai_service import get_ai_response, get_small_talk_response
from app.services.google_calendar import GoogleCalendarService
from app.api.models import TelegramUpdate
from app.services.conversation import conversation_state
from app.agent.nlp_agent import NLPAgent

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()
telegram_service = TelegramBotService()
calendar_service = GoogleCalendarService()
nlp_agent = NLPAgent()

access_token = None


@router.post("/webhook")
async def telegram_webhook(update: TelegramUpdate):
    """Handle incoming Telegram messages"""
    
    # logger.info(f"------------------------------------>Received update: {update}")
    if not update.message:
        return {"status": "ok"}
    
    chat_id = update.message["chat"]["id"]
    user_message = None
    message_type = "text"
    
    # Handle different message types
    if "text" in update.message:
        user_message = update.message["text"]
    
    if not user_message:
        await send_telegram_message(
            chat_id,
            "I'm sorry, I didn't understand that. Can you please rephrase your message?"
        )
        return {"status": "ok"}
    
    
    auth_check = calendar_service.is_authenticated()
    test = calendar_service.list_calendars()
    # logger.info(f"------------------------------------>Test: {test}")

    
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
    logger.info(f"------------------>RELEVANCY:{relevancy_result}")
    if not relevancy_result["relevant"]:
        ai_response = await get_small_talk_response(user_message, history)
        await send_telegram_message(chat_id, ai_response)
        conversation_state.add_message(chat_id, "assistant", ai_response)
        return {"status": "ok"}  
    
    
    try:
        event_data = await nlp_agent.extract_intent(user_message, history)
        # logger.info(f"===========> Event data: {event_data}")

        # If no confirmation is needed, proceed with the action
        if event_data["confirmation_needed"] is False:
            if event_data["intent"] == "create":
                # Create event in Google Calendar
                calendar_response = calendar_service.create_event(event_data)
                if calendar_response["success"]:
                    await send_telegram_message(
                        chat_id, f"Event created successfully! Here's the link to your event: {calendar_response['event_link']}"
                    )
                return {"status": "ok"}

            elif event_data["intent"] in ["update", "delete"]:
                # Query events based on event details (using the same query for both update and delete)
                matched_events = calendar_service.query_events({
                    "event_name": event_data.get("event_name", ""),
                    "date": event_data.get("date", "")
                })

                if not matched_events["success"] or not matched_events["events"]:
                    response = "No matching events found."
                    await send_telegram_message(chat_id, response)
                    conversation_state.add_message(chat_id, "assistant", response)
                    return {"status": "ok"}

                events = matched_events["events"]
                # logger.info(f"================> Matched events: {events}")
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
                        calendar_response = calendar_service.update_event(event_id, event_data)
                        if calendar_response["success"]:
                            await send_telegram_message(
                                chat_id, f"Event updated successfully! Here's the link to your event: {calendar_response['event_link']}"
                            )
                    elif event_data["intent"] == "delete":
                        calendar_response = calendar_service.delete_event(event_id)
                        logger.info(f"DELETE{calendar_response}")
                        if calendar_response["success"]:
                            await send_telegram_message(chat_id, "Event deleted successfully!")
                # Add AI response to conversation history
                conversation_state.add_message(chat_id, "assistant", ai_response)
                return {"status": "ok"}

            elif event_data["intent"] == "query":
                # Query events in Google Calendar based on the event details
                matched_events = calendar_service.query_events({
                    "event_name": event_data.get("event_name", ""),
                    "date": event_data.get("date", "")
                })

                if not matched_events["success"] or not matched_events["events"]:
                    await send_telegram_message(chat_id, "No matching events found.")
                    return {"status": "ok"}

                events = matched_events["events"]
                # logger.info(f"================> Matched events: {events}")

                if len(events) == 1:
                    event_id = events[0]["id"]
                    ai_response = await get_ai_response(events[0], history)
                    await send_telegram_message(chat_id, ai_response)
                else:
                    event_list = "\n".join(
                        [f"{idx + 1}. {event['summary']} - {event['start']}" for idx, event in enumerate(events)]
                    )
                    ai_response = await get_ai_response(event_list, history)
                    await send_telegram_message(chat_id, ai_response)
                # Add AI response to conversation history
                conversation_state.add_message(chat_id, "assistant", ai_response)
                return {"status": "ok"}

        # In case confirmation is needed (handling as needed)
        ai_response = await get_ai_response(event_data, history)
        # Add AI response to conversation history
        conversation_state.add_message(chat_id, "assistant", ai_response)
        await send_telegram_message(chat_id, ai_response)
        return {"status": "ok"}
            
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
