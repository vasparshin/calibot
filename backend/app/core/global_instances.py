"""
Global service instances for CaliBOT.

Provides centralized access to shared service instances to avoid
circular imports and ensure consistent state management.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global instances - initialized on first access
_global_queue_handler: Optional[object] = None
_services_initialized = False

def get_global_queue_handler():
    """Get the global EventQueueHandler instance."""
    global _global_queue_handler, _services_initialized
    
    if not _services_initialized:
        initialize_global_services()
    
    return _global_queue_handler

def initialize_global_services():
    """Initialize all global service instances."""
    global _global_queue_handler, _services_initialized
    
    if _services_initialized:
        return
    
    try:
        # Import here to avoid circular imports
        from app.services.telegram import TelegramBotService
        from app.services.google_calendar import GoogleCalendarService
        from app.services.conversation import conversation_state
        from app.services.event_queue_handler import EventQueueHandler
        from app.agent.calendar_agent import CalendarAgent
        
        # Initialize services
        telegram_service = TelegramBotService()
        calendar_service = GoogleCalendarService()
        calendar_agent = CalendarAgent()
        
        # Create global queue handler
        _global_queue_handler = EventQueueHandler(
            telegram_service, 
            conversation_state, 
            calendar_service, 
            calendar_agent
        )
        
        _services_initialized = True
        logger.info("✅ Global services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize global services: {e}")
        raise

def reset_global_services():
    """Reset global services (for testing)."""
    global _global_queue_handler, _services_initialized
    _global_queue_handler = None
    _services_initialized = False
