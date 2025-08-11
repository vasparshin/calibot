import httpx
from app.config import TELEGRAM_API_TOKEN

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}"

def strip_markdown(text: str) -> str:
    """Remove Markdown formatting characters from text, but preserve hyperlinks"""
    import re
    # Remove bold **text**
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove italic *text* (but not hyperlinks)
    text = re.sub(r'(?<!\])\*(.*?)\*(?!\()', r'\1', text)
    # Remove other common markdown
    text = re.sub(r'`(.*?)`', r'\1', text)  # code
    text = re.sub(r'_(.*?)_', r'\1', text)  # underline
    # Keep hyperlinks [text](url) intact
    return text

async def send_telegram_message(chat_id: int, text: str, parse_mode: str = None, reply_markup: dict = None):
        """Send message to Telegram chat with optional inline keyboard"""
        # Check if text contains hyperlinks - if so, use Markdown mode
        if '[' in text and '](' in text and ')' in text:
            parse_mode = "Markdown"
            clean_text = strip_markdown(text)  # This now preserves hyperlinks
        else:
            # Strip all markdown formatting for plain text
            clean_text = strip_markdown(text)
            
        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": chat_id,
                "text": clean_text,
                "disable_web_page_preview": True  # Disable Google Workspace banner previews
            }
            # Only add parse_mode if specified
            if parse_mode:
                payload["parse_mode"] = parse_mode
            
            # Add inline keyboard if provided
            if reply_markup:
                payload["reply_markup"] = reply_markup
                
            response = await client.post(
                f"{TELEGRAM_API_BASE}/sendMessage",
                json=payload
            )
            return response.json()


def create_event_selection_keyboard(events: list) -> dict:
    """Create inline keyboard for selecting individual events"""
    keyboard = []
    
    # Add event buttons (max 5 per row, limit to first 20 events)
    events_to_show = events[:20]
    for i, event in enumerate(events_to_show, 1):
        event_name = event.get('summary', f'Event {i}')[:30]  # Truncate long names
        keyboard.append([{"text": f"{i}. {event_name}", "callback_data": f"select_event_{i-1}"}])
    
    # Add control buttons
    keyboard.append([
        {"text": "✅ Select All", "callback_data": "select_all"},
        {"text": "❌ Cancel", "callback_data": "select_cancel"}
    ])
    
    return {"inline_keyboard": keyboard}

async def answer_callback_query(callback_query_id: str, text: str = None, show_alert: bool = False):
    """Answer callback query from inline keyboard button press"""
    async with httpx.AsyncClient() as client:
        payload = {
            "callback_query_id": callback_query_id,
        }
        if text:
            payload["text"] = text
        if show_alert:
            payload["show_alert"] = show_alert
            
        response = await client.post(
            f"{TELEGRAM_API_BASE}/answerCallbackQuery",
            json=payload
        )
        return response.json()

async def edit_message_text(chat_id: int, message_id: int, text: str, parse_mode: str = None, reply_markup: dict = None):
    """Edit existing message text and keyboard"""
    async with httpx.AsyncClient() as client:
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
            
        response = await client.post(
            f"{TELEGRAM_API_BASE}/editMessageText",
            json=payload
        )
        return response.json()


class TelegramBotService:
    def start(self):
        print("Telegram bot started...")  # For debugging

    def stop(self):
        print("Telegram bot stopped...")  # For debugging
        
    
    

        
        

        
        

