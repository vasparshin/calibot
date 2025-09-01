#!/usr/bin/env python3
"""
Deployment Notification System for CaliBOT

Sends notification to Telegram group when new deployment is detected.
Can be run manually or integrated into CI/CD pipeline.
"""

import asyncio
import httpx
import os
import sys
from datetime import datetime

# Configuration
GROUP_CHAT_ID = -4627994150  # CaliBOT test group
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

if not TELEGRAM_API_TOKEN:
    print("❌ TELEGRAM_API_TOKEN environment variable not set")
    sys.exit(1)

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}"

def get_current_version():
    """Get current version from __init__.py file."""
    try:
        init_file = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', '__init__.py')
        with open(init_file, 'r') as f:
            for line in f:
                if line.startswith('__version__'):
                    # Extract version string from __version__ = "x.y.z"
                    return line.split('"')[1]
        return "unknown"
    except Exception as e:
        print(f"⚠️ Could not read version: {e}")
        return "unknown"

async def send_deployment_notification():
    """Send deployment notification to the group chat."""
    try:
        current_version = get_current_version()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        message = f"""🚀 **CaliBOT Deployment Notification**

📦 **Version**: {current_version}
⏰ **Deployed**: {timestamp}
🔧 **Status**: Live and ready for testing
🧪 **Test Group**: This chat (-4627994150)

✅ **Ready for testing!**

---
*This is an automated deployment notification. You can now test the latest features and bug fixes.*"""

        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": GROUP_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            response = await client.post(
                f"{TELEGRAM_API_BASE}/sendMessage",
                json=payload
            )
            
            if response.status_code == 200:
                print(f"✅ Deployment notification sent successfully for version {current_version}")
                return True
            else:
                print(f"❌ Failed to send notification: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error sending deployment notification: {e}")
        return False

async def check_and_notify_if_new_deployment():
    """Check if this is a new deployment and send notification if so."""
    # For now, always send notification when script is run
    # In future, this could check against a stored version file
    await send_deployment_notification()

if __name__ == "__main__":
    print("🚀 CaliBOT Deployment Notifier")
    print("=" * 40)
    
    # Run the notification
    asyncio.run(check_and_notify_if_new_deployment())
