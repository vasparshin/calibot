"""
Self-Monitoring Deployment Notifier for CaliBOT

Monitors deployment status and sends notifications to the test group
when new versions are successfully deployed and ready for testing.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import os

from app.services.telegram import send_telegram_message
from app import __version__

logger = logging.getLogger(__name__)

class DeploymentMonitor:
    """Monitors deployment status and sends notifications."""
    
    def __init__(self):
        self.group_chat_id = -4627994150  # CaliBOT test group
        self.last_notified_version = None
        self.startup_time = datetime.now()
        
    async def check_and_notify_deployment(self):
        """Check if this is a new deployment and send notification if needed."""
        try:
            current_version = __version__
            
            # Only notify if this is a different version than last notified
            if self.last_notified_version != current_version:
                # Wait a moment after startup to ensure everything is ready
                time_since_startup = datetime.now() - self.startup_time
                if time_since_startup < timedelta(seconds=10):
                    await asyncio.sleep(10 - time_since_startup.total_seconds())
                
                await self.send_deployment_notification(current_version)
                self.last_notified_version = current_version
                logger.info(f"✅ Deployment notification sent for version {current_version}")
            
        except Exception as e:
            logger.error(f"Error in deployment monitor: {e}")
    
    async def send_deployment_notification(self, version: str):
        """Send deployment notification to the test group."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            message = f"""🚀 **CaliBOT Deployment Notification**

📦 **Version**: {version}
⏰ **Deployed**: {timestamp}
🔧 **Status**: Live and ready for testing
🧪 **Test Group**: This chat (-4627994150)

✅ **Ready for testing!**

---
*Automated deployment notification - test the latest features and bug fixes.*"""

            result = await send_telegram_message(
                chat_id=self.group_chat_id,
                text=message,
                parse_mode="Markdown"
            )
            
            if result and result.get("ok"):
                logger.info(f"✅ Deployment notification sent successfully for version {version}")
                return True
            else:
                logger.warning(f"⚠️ Deployment notification may have failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending deployment notification: {e}")
            return False

# Global instance
deployment_monitor = DeploymentMonitor()

async def notify_deployment_ready():
    """Convenience function to trigger deployment notification."""
    await deployment_monitor.check_and_notify_deployment()
