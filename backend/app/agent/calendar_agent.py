from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class CalendarAgent:
    def __init__(self):
        self.calendar_cache = {}  # Cache for available calendars
        
    def update_calendar_cache(self, calendars: List[Dict]):
        """Update the internal cache of available calendars"""
        self.calendar_cache = {
            cal['id']: {
                'id': cal['id'],
                'name': cal.get('summary', 'Unknown'),
                'description': cal.get('description', ''),
                'primary': cal.get('primary', False),
                'color': cal.get('backgroundColor', '#ffffff'),
                'themes': []  # Themes removed - LLM handles calendar selection
            }
            for cal in calendars
        }
        logger.info(f"Updated calendar cache with {len(self.calendar_cache)} calendars")

    def update_single_calendar_cache(self, calendar_id: str, calendar_data: Dict):
        """Update a single calendar in the cache"""
        if not self.calendar_cache:
            self.calendar_cache = {}
        
        self.calendar_cache[calendar_id] = {
            'id': calendar_id,
            'name': calendar_data.get('name', calendar_data.get('summary', 'Unknown')),
            'description': calendar_data.get('description', ''),
            'primary': calendar_data.get('primary', False),
            'color': calendar_data.get('backgroundColor', '#ffffff'),
            'themes': []  # Themes removed - LLM handles calendar selection
        }
        logger.info(f"Updated single calendar cache for {calendar_id}")
        
        
    def find_calendar_by_name(self, calendar_name: str) -> Optional[str]:
        """
        Find calendar ID by name (case insensitive partial match).
        Used for user-specified calendar names.
        """
        if not calendar_name or not self.calendar_cache:
            return None
            
        calendar_name_lower = calendar_name.lower()
        
        for cal_id, cal_info in self.calendar_cache.items():
            if (calendar_name_lower in cal_info['name'].lower() or 
                cal_info['name'].lower() in calendar_name_lower):
                return cal_id
                
        return None
        
        

        
    def get_calendar_suggestions(self, query: str = "") -> List[Dict]:
        """Get list of calendars for user selection (simplified - no AI scoring)"""
        if not self.calendar_cache:
            return []
            
        calendars = []
        for cal_id, cal_info in self.calendar_cache.items():
            calendars.append({
                'id': cal_id,
                'name': cal_info['name'],
                'primary': cal_info['primary']
            })
            
        return calendars

    def get_calendar_info(self, calendar_id: str) -> Optional[Dict]:
        """Get information about a specific calendar"""
        return self.calendar_cache.get(calendar_id)
        
    def list_all_calendars(self) -> List[Dict]:
        """Get all cached calendars"""
        return list(self.calendar_cache.values())
