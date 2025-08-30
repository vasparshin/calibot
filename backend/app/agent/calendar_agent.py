from typing import Dict, List, Optional
from litellm import acompletion
from app.config import LITELLM_MODEL
import json
import logging
import re

logger = logging.getLogger(__name__)

class CalendarAgent:
    def __init__(self):
        self.model = LITELLM_MODEL
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
                'themes': self._extract_themes_from_name(cal.get('summary', ''))
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
            'themes': self._extract_themes_from_name(calendar_data.get('name', calendar_data.get('summary', '')))
        }
        logger.info(f"Updated single calendar cache for {calendar_id}")
        
    def _extract_themes_from_name(self, calendar_name: str) -> List[str]:
        """Extract potential themes from calendar name"""
        themes = []
        name_lower = calendar_name.lower()
        
        # Common theme patterns
        theme_patterns = {
            'work': ['work', 'office', 'business', 'professional', 'meetings', 'corporate'],
            'personal': ['personal', 'private', 'life', 'family'],
            'sports': ['sports', 'fitness', 'gym', 'exercise', 'workout', 'training', 'football', 'basketball', 'tennis', 'running'],
            'education': ['lessons', 'school', 'university', 'education', 'learning', 'study', 'class', 'course', 'tutor'],
            'health': ['health', 'medical', 'doctor', 'dentist', 'appointment', 'hospital', 'clinic'],
            'travel': ['travel', 'trip', 'vacation', 'holiday', 'flight'],
            'social': ['social', 'friends', 'party', 'event', 'dinner', 'lunch'],
            'hobbies': ['hobby', 'music', 'art', 'reading', 'gaming']
        }
        
        # NO KEYWORD-BASED MATCHING - per PROJECT_RULES.md
        # LLM should provide calendar selection directly
        # Theme matching removed - calendars should be selected by LLM
                
        return themes
        
    async def select_calendar_for_event(self, event_data: Dict) -> Optional[str]:
        """
        Intelligently select the best calendar for an event based on content and available calendars
        """
        if not self.calendar_cache:
            logger.warning("No calendars in cache, defaulting to primary")
            return 'primary'
            
        # Check if user specified a calendar
        if 'calendar' in event_data or 'calendar_name' in event_data:
            specified_calendar = event_data.get('calendar') or event_data.get('calendar_name')
            calendar_id = self._find_calendar_by_name(specified_calendar)
            if calendar_id:
                return calendar_id
                
        # Use AI to analyze event and suggest calendar
        try:
            calendar_suggestion = await self._ai_suggest_calendar(event_data)
            if calendar_suggestion:
                return calendar_suggestion
        except Exception as e:
            logger.error(f"Error in AI calendar suggestion: {e}")

        # NO FALLBACK FUNCTIONALITY - per PROJECT_RULES.md
        # If AI calendar suggestion fails, default to primary calendar
        # LLM should provide calendar information through proper prompting
        logger.warning("AI calendar suggestion failed, defaulting to primary calendar")
        return 'primary'
        
    def _find_calendar_by_name(self, calendar_name: str) -> Optional[str]:
        """Find calendar ID by name (case insensitive partial match)"""
        if not calendar_name:
            return None
            
        calendar_name_lower = calendar_name.lower()
        
        for cal_id, cal_info in self.calendar_cache.items():
            if (calendar_name_lower in cal_info['name'].lower() or 
                cal_info['name'].lower() in calendar_name_lower):
                return cal_id
                
        return None
        
    async def _ai_suggest_calendar(self, event_data: Dict) -> Optional[str]:
        """Use AI to suggest the best calendar based on event content"""
        
        # Prepare calendar options for AI
        calendar_options = []
        for cal_id, cal_info in self.calendar_cache.items():
            calendar_options.append({
                'id': cal_id,
                'name': cal_info['name'],
                'themes': cal_info['themes'],
                'primary': cal_info['primary']
            })
            
        system_prompt = f"""You are a calendar organization expert. Based on the event details and available calendars, select the most appropriate calendar.

Available Calendars:
{json.dumps(calendar_options, indent=2)}

Rules:
1. Match event content with calendar themes/names
2. Consider calendar purpose (work, personal, sports, etc.)
3. If no clear match, prefer primary calendar
4. Return only the calendar ID, nothing else

Event to analyze: {json.dumps(event_data, indent=2)}

Respond with only the calendar ID (e.g., "primary" or the specific calendar ID)."""

        try:
            response = await acompletion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Select the best calendar for this event."}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            suggested_id = response['choices'][0]['message']['content'].strip().strip('"\'')
            
            # Validate the suggested ID exists
            if suggested_id in self.calendar_cache or suggested_id == 'primary':
                logger.info(f"AI suggested calendar: {suggested_id}")
                return suggested_id
                
        except Exception as e:
            logger.error(f"AI calendar suggestion failed: {e}")
            
        return None
        

        
    def get_calendar_suggestions(self, query: str = "") -> List[Dict]:
        """Get list of calendars with relevance scoring for user selection"""
        if not query:
            return [
                {
                    'id': cal_id,
                    'name': cal_info['name'],
                    'themes': cal_info['themes'],
                    'primary': cal_info['primary'],
                    'relevance': 'default'
                }
                for cal_id, cal_info in self.calendar_cache.items()
            ]
            
        # Score calendars based on query relevance
        scored_calendars = []
        query_lower = query.lower()
        
        for cal_id, cal_info in self.calendar_cache.items():
            relevance_score = 0
            
            # Name matching
            if query_lower in cal_info['name'].lower():
                relevance_score += 5
                
            # Theme matching
            for theme in cal_info['themes']:
                if theme in query_lower:
                    relevance_score += 3
                    
            scored_calendars.append({
                'id': cal_id,
                'name': cal_info['name'],
                'themes': cal_info['themes'],
                'primary': cal_info['primary'],
                'relevance_score': relevance_score,
                'relevance': 'high' if relevance_score >= 5 else 'medium' if relevance_score >= 3 else 'low'
            })
            
        # Sort by relevance score
        scored_calendars.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_calendars

    def get_calendar_info(self, calendar_id: str) -> Optional[Dict]:
        """Get information about a specific calendar"""
        return self.calendar_cache.get(calendar_id)
        
    def list_all_calendars(self) -> List[Dict]:
        """Get all cached calendars"""
        return list(self.calendar_cache.values())
