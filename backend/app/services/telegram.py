import httpx
from app.config import TELEGRAM_API_TOKEN

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}"

def strip_markdown(text: str) -> str:
    """Remove Markdown formatting characters from text"""
    import re
    # Remove bold **text**
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove italic *text*
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Remove other common markdown
    text = re.sub(r'`(.*?)`', r'\1', text)  # code
    text = re.sub(r'_(.*?)_', r'\1', text)  # underline
    return text

async def send_telegram_message(chat_id: int, text: str, parse_mode: str = None):
        """Send message to Telegram chat"""
        # Strip markdown formatting to show plain text
        clean_text = strip_markdown(text)
        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": chat_id,
                "text": clean_text,
            }
            # Only add parse_mode if specified
            if parse_mode:
                payload["parse_mode"] = parse_mode
                
            response = await client.post(
                f"{TELEGRAM_API_BASE}/sendMessage",
                json=payload
            )
            return response.json()


class TelegramBotService:
    def start(self):
        print("Telegram bot started...")  # For debugging

    def stop(self):
        print("Telegram bot stopped...")  # For debugging
        
    
    

        
        

        
        

