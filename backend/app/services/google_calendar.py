from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import os
import pickle
import traceback
import asyncio
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from app.config import (
    GOOGLE_CLIENT_SECRET_FILE, 
    GOOGLE_API_SCOPES, 
    API_HOST, 
    API_PORT,
    OAUTH_REDIRECT_PATH
)
from app.agent.calendar_agent import CalendarAgent
import logging

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    def __init__(self):
        self.credentials = None
        self.token_path = '/data/token.pickle'
        self.service = None
        self.redirect_uri = os.getenv("BACKEND_URL", f"http://{API_HOST}:{API_PORT}") + OAUTH_REDIRECT_PATH
        self.calendar_agent = CalendarAgent()
        self._calendars_loaded = False
    
    def get_auth_url(self, force_fresh=True):
        """Generate OAuth authorization URL with proper parameters
        
        Args:
            force_fresh: If True, ensures a fresh URL with no caching issues
        """
        try:
            # Create a fresh Flow instance every time to avoid any caching issues
            flow = Flow.from_client_secrets_file(
                GOOGLE_CLIENT_SECRET_FILE,
                scopes=GOOGLE_API_SCOPES,
                redirect_uri=self.redirect_uri
            )
            logger.info(f"Redirect URI: {flow.redirect_uri}")
            
            # Generate authorization URL with explicit parameters
            # CRITICAL FIX: Explicitly include response_type=code to prevent recurring OAuth errors
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                response_type='code'  # Explicitly specify response_type
            )
            
            # Enhanced logging for OAuth debugging
            logger.info(f"OAuth URL generated: {auth_url[:100]}...")
            logger.info(f"OAuth URL contains response_type: {'response_type' in auth_url}")
            logger.info(f"OAuth URL contains response_type=code: {'response_type=code' in auth_url}")
            
            # Double-check and ensure response_type=code is present
            if 'response_type=code' not in auth_url:
                # This should never happen with google-auth-oauthlib, but adding as failsafe
                separator = '&' if '?' in auth_url else '?'
                auth_url += f'{separator}response_type=code'
                logger.warning("CRITICAL: Had to manually add missing response_type=code parameter to OAuth URL")
                logger.warning(f"Original URL was: {auth_url[:100]}...")
            else:
                logger.info("✅ OAuth URL correctly contains response_type=code parameter")
            
            # Add cache-busting parameter if force_fresh is True
            if force_fresh:
                import time
                cache_buster = int(time.time())
                separator = '&' if '?' in auth_url else '?'
                auth_url += f'{separator}_cb={cache_buster}'
                logger.info(f"Added cache-busting parameter: _cb={cache_buster}")
            
            logger.info(f"Generated fresh auth URL: {auth_url[:120]}...")
            
            # Store the state for later validation
            with open("oauth_state.txt", "w") as f:
                f.write(state)

            # Store client config for callback processing
            with open("client_config.pickle", "wb") as f:
                pickle.dump({
                    "client_secrets_file": GOOGLE_CLIENT_SECRET_FILE, 
                    "scopes": GOOGLE_API_SCOPES, 
                    "redirect_uri": self.redirect_uri
                }, f)

            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            logger.error(f"Redirect URI: {getattr(self, 'redirect_uri', 'Not set')}")
            logger.error(f"Client secrets file: {GOOGLE_CLIENT_SECRET_FILE}")
            raise

    async def handle_oauth_callback(self, request: Request):
        """Handle the OAuth callback and exchange code for token"""
        code = request.query_params.get('code')
        state = request.query_params.get('state')

        if not code:
            logger.error("Missing authorization code in OAuth callback")
            raise HTTPException(status_code=400, detail="Missing authorization code")

        # Be more forgiving about state validation for production deployments
        try:
            with open('oauth_state.txt', 'r') as f:
                saved_state = f.read()
            with open('client_config.pickle', 'rb') as f:
                client_config = pickle.load(f)
        except FileNotFoundError as e:
            logger.warning(f"OAuth state files not found (likely server restart): {e}")
            # Use current configuration
            client_config = {
                "client_secrets_file": GOOGLE_CLIENT_SECRET_FILE, 
                "scopes": GOOGLE_API_SCOPES, 
                "redirect_uri": self.redirect_uri
            }
            saved_state = None

        # Validate state if both are available
        if state and saved_state and state != saved_state:
            logger.warning(f"State parameter mismatch: received {state}, saved {saved_state}")
            # For production stability, continue anyway - the auth code provides security

        try:
            flow = Flow.from_client_secrets_file(
                client_config["client_secrets_file"],
                scopes=client_config["scopes"],
                redirect_uri=client_config["redirect_uri"]
            )
            flow.fetch_token(code=code)
            self.credentials = flow.credentials

            with open(self.token_path, 'wb') as token:
                pickle.dump(self.credentials, token)

            self.service = build('calendar', 'v3', credentials=self.credentials)
            
            html_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Authentication Successful</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            text-align: center;
                            margin-top: 50px;
                        }
                        .container {
                            max-width: 500px;
                            margin: auto;
                            padding: 20px;
                            border: 1px solid #ddd;
                            border-radius: 10px;
                            box-shadow: 2px 2px 12px rgba(0, 0, 0, 0.1);
                        }
                        h2 {
                            color: #4CAF50;
                        }
                        p {
                            font-size: 16px;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Authentication Successful</h2>
                        <p>You can now close this tab and return to Telegram.</p>
                    </div>
                </body>
                </html>
                """

            return HTMLResponse(content=html_content, status_code=200)

        except Exception as e:
            logger.error(f"Error during token exchange: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail="Failed to authenticate")

    def get_calendar_service(self):
        """Get an authenticated Google Calendar service."""
        if self.service:
            logger.info("Using existing service instance.")
            return self.service

        # Load existing credentials if available
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    self.credentials = pickle.load(token)
            except Exception as e:
                logger.info(f"Error loading credentials: {e}")
                if os.path.exists(self.token_path): 
                    os.remove(self.token_path)
                return None  # Force re-authentication

        # If credentials are valid, use them
        if self.credentials and self.credentials.valid:
            logger.info("Loaded valid credentials.")
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return self.service

        # If credentials are expired but refreshable, refresh them
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                logger.info("Refreshing expired credentials...")
                self.credentials.refresh(GoogleRequest())
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.credentials, token)
                logger.info("Credentials refreshed successfully.")
                self.service = build('calendar', 'v3', credentials=self.credentials)
                return self.service
            except Exception as e:
                logger.info(f"Failed to refresh credentials: {e}")
                if os.path.exists(self.token_path):
                    os.remove(self.token_path)  # Remove invalid credentials
                return None

        # If no valid credentials are found, require authentication
        logger.info("No valid credentials found. User must reauthenticate.")
        return None

    def _handle_api_call(self, api_call_func, *args, **kwargs):
        """Helper method to handle API calls with proper error handling for expired credentials"""
        try:
            return api_call_func(*args, **kwargs)
        except Exception as e:
            if "invalid_grant" in str(e) or "Token has been expired or revoked" in str(e):
                logger.error(f"Credentials expired during API call: {e}")
                # Force re-authentication by clearing credentials
                if os.path.exists(self.token_path):
                    os.remove(self.token_path)
                self.credentials = None
                self.service = None
                raise HTTPException(status_code=401, detail="Authentication expired. Please log in again.")
            else:
                logger.error(f"API call failed: {e}")
                raise e
    
    def is_authenticated(self):
        """Check if the user is authenticated"""
        return self.get_calendar_service() is not None

    async def ensure_calendars_loaded(self):
        """Ensure calendars are loaded into the calendar agent"""
        if not self._calendars_loaded and self.is_authenticated():
            try:
                calendars = self.list_calendars()
                if isinstance(calendars, list):
                    self.calendar_agent.update_calendar_cache(calendars)
                    self._calendars_loaded = True
                    logger.info(f"Loaded {len(calendars)} calendars into calendar agent")
            except Exception as e:
                logger.error(f"Failed to load calendars: {e}")

    async def get_available_calendars(self) -> List[Dict]:
        """Get all available calendars with theme information"""
        await self.ensure_calendars_loaded()
        return self.calendar_agent.list_all_calendars()

    async def suggest_calendar(self, event_data: Dict, query: str = "") -> List[Dict]:
        """Get calendar suggestions based on event data or query"""
        await self.ensure_calendars_loaded()
        if event_data:
            suggested_id = await self.calendar_agent.select_calendar_for_event(event_data)
            # Return the suggested calendar with high relevance, plus others
            suggestions = self.calendar_agent.get_calendar_suggestions(query)
            # Move suggested calendar to top
            for i, cal in enumerate(suggestions):
                if cal['id'] == suggested_id:
                    suggestions[0], suggestions[i] = suggestions[i], suggestions[0]
                    suggestions[0]['relevance'] = 'suggested'
                    break
            return suggestions
        else:
            return self.calendar_agent.get_calendar_suggestions(query)
    

    def get_user_timezone(self):
        """Fetch the user's time zone from Google Calendar settings."""
        service = self.get_calendar_service()
        if not service:
            return 'UTC'  # Default to UTC if authentication fails

        try:
            settings = self._handle_api_call(
                lambda: service.settings().get(setting='timezone').execute()
            )
            return settings.get('value', 'UTC')
        except Exception as e:
            logger.info(f"Failed to retrieve user time zone: {e}")
            return 'UTC'

    def get_calendar_display_name(self, calendar_id: str) -> str:
        """Get the actual display name for a calendar from Google Calendar API"""
        if not calendar_id:
            return "Unknown Calendar"
        
        # Handle primary calendar
        if calendar_id == 'primary':
            return "Personal"
        
        # Try to get from calendar agent cache first
        calendar_info = self.calendar_agent.get_calendar_info(calendar_id)
        if calendar_info and calendar_info.get('name'):
            return calendar_info['name']
        
        # Fallback to API call
        service = self.get_calendar_service()
        if not service:
            return calendar_id  # Return ID if no service available
        
        try:
            calendar = self._handle_api_call(
                lambda: service.calendars().get(calendarId=calendar_id).execute()
            )
            display_name = calendar.get('summary', calendar_id)
            
            # Update cache with new information
            self.calendar_agent.update_single_calendar_cache(calendar_id, {
                'name': display_name,
                'id': calendar_id
            })
            
            return display_name
        except Exception as e:
            logger.warning(f"Failed to get calendar name for {calendar_id}: {e}")
            return calendar_id  # Return ID when name lookup fails
    
    async def create_event(self, event_data):
        """Create a new event in Google Calendar with intelligent calendar selection"""
        service = self.get_calendar_service()
        if not service:
            return {
                'success': False,
                'message': 'Authentication required',
                'auth_required': True
            }
        
        # Ensure calendars are loaded for intelligent selection
        await self.ensure_calendars_loaded()
        
        # Intelligently select calendar
        selected_calendar_id = await self.calendar_agent.select_calendar_for_event(event_data)
        
        # Get user's time zone
        user_timezone = self.get_user_timezone()
        start_time = event_data.get('start_time')
        end_time = event_data.get('end_time')
        date = event_data.get('date')

        # If end_time is missing, set it to 30 minutes after start_time
        if start_time and not end_time:
            try:
                start_dt = datetime.strptime(f"{date}T{start_time}", "%Y-%m-%dT%H:%M")
                end_dt = start_dt + timedelta(minutes=30)
                end_time = end_dt.strftime("%H:%M")
            except Exception as e:
                return {
                    'success': False,
                    'message': f'Invalid start time or date: {e}'
                }

        if not start_time or not end_time:
            return {
                'success': False,
                'message': 'Start time and end time are required.'
            }        
        event = {
            'summary': event_data.get('event_name', 'Untitled Event'),
            'description': event_data.get('description', ''),
            'start': {
                'dateTime': f"{date}T{start_time}:00",
                'timeZone': user_timezone,
            },
            'end': {
                'dateTime': f"{date}T{end_time}:00",
                'timeZone': user_timezone,
            },
        }
        
        # Add attendees if specified
        if event_data.get('participants'):
            participants = event_data.get('participants', [])
            valid_attendees = []
            for participant in participants:
                # Only add participants that look like email addresses
                if isinstance(participant, str) and '@' in participant:
                    valid_attendees.append({'email': participant})
                else:
                    logger.info(f"Skipping participant '{participant}' - not a valid email")
            
            if valid_attendees:
                event['attendees'] = valid_attendees
                logger.info(f"Added {len(valid_attendees)} attendees to event")
            
        # Get calendar name for logging
        calendar_info = self.calendar_agent.get_calendar_info(selected_calendar_id)
        calendar_name = calendar_info['name'] if calendar_info else selected_calendar_id
        
        logger.info(f"Creating event '{event['summary']}' in calendar '{calendar_name}' ({selected_calendar_id})")
        logger.info(f"Event object: {event}")
        
        try:
            created_event = self._handle_api_call(
                lambda: service.events().insert(calendarId=selected_calendar_id, body=event).execute()
            )
            return {
                'success': True,
                'event_id': created_event['id'],
                'event_link': created_event['htmlLink'],
                'calendar_used': calendar_name,
                'calendar_id': selected_calendar_id
            }
        except HTTPException:
            # Re-raise authentication errors
            raise
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            return {
                'success': False,
                'message': f'Failed to create event: {str(e)}'
            }
    
    def update_event(self, event_id, event_data, source_calendar_id=None):
        """Update an existing event in Google Calendar, with support for moving between calendars"""
        service = self.get_calendar_service()
        if not service:
            return {
                'success': False,
                'message': 'Authentication required',
                'auth_required': True
            }
        try:
            # Use provided calendar ID or default to primary
            calendar_id = source_calendar_id or 'primary'
            
            # First retrieve the event from the source calendar
            event = self._handle_api_call(
                lambda: service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            )
            
            # Check if we need to move to a different calendar
            target_calendar_id = calendar_id  # Default to same calendar
            if 'calendar' in event_data or 'calendar_name' in event_data:
                specified_calendar = event_data.get('calendar') or event_data.get('calendar_name')
                logger.info(f"Calendar move requested to: '{specified_calendar}'")
                
                # Use calendar agent if available and loaded
                if hasattr(self, 'calendar_agent') and self.calendar_agent.calendar_cache:
                    logger.info(f"Calendar agent available with {len(self.calendar_agent.calendar_cache)} calendars")
                    new_calendar_id = self.calendar_agent._find_calendar_by_name(specified_calendar)
                    logger.info(f"Calendar lookup result for '{specified_calendar}': {new_calendar_id}")
                    
                    if new_calendar_id and new_calendar_id != calendar_id:
                        target_calendar_id = new_calendar_id
                        logger.info(f"Moving event from '{calendar_id}' to '{new_calendar_id}'")
                    elif new_calendar_id == calendar_id:
                        logger.info(f"Event already in target calendar '{calendar_id}'")
                    else:
                        logger.warning(f"Could not find calendar '{specified_calendar}' - staying in '{calendar_id}'")
                else:
                    logger.error(f"Calendar agent not available or cache empty - cannot move to '{specified_calendar}'")
                    # Try to update calendar cache
                    if hasattr(self, 'calendar_agent'):
                        try:
                            calendars = self.get_calendars()
                            if calendars:
                                self.calendar_agent.update_calendar_cache(calendars)
                                logger.info(f"Updated calendar cache with {len(calendars)} calendars")
                                new_calendar_id = self.calendar_agent._find_calendar_by_name(specified_calendar)
                                if new_calendar_id and new_calendar_id != calendar_id:
                                    target_calendar_id = new_calendar_id
                                    logger.info(f"After cache update - moving event from '{calendar_id}' to '{new_calendar_id}'")
                        except Exception as e:
                            logger.error(f"Failed to update calendar cache: {e}")
            
            # Update fields
            if 'event_name' in event_data:
                event['summary'] = event_data['event_name']
            if 'description' in event_data:
                event['description'] = event_data['description']
            
            # Handle datetime updates - support both ISO format and date+time format
            # CRITICAL FIX: Handle date-only updates (moving event to different date)
            if 'date' in event_data and 'start_time' not in event_data and 'end_time' not in event_data:
                new_date = event_data['date']
                logger.info(f"CALENDAR SERVICE: Moving event to new date: {new_date}")
                
                # Extract existing times and apply to new date
                existing_start = event.get('start', {}).get('dateTime', '')
                existing_end = event.get('end', {}).get('dateTime', '')
                
                if existing_start and 'T' in existing_start:
                    start_time_part = existing_start.split('T')[1]  # Keep time part
                    event['start']['dateTime'] = f"{new_date}T{start_time_part}"
                    logger.info(f"CALENDAR SERVICE: Updated start to {event['start']['dateTime']}")
                
                if existing_end and 'T' in existing_end:
                    end_time_part = existing_end.split('T')[1]  # Keep time part
                    event['end']['dateTime'] = f"{new_date}T{end_time_part}"
                    logger.info(f"CALENDAR SERVICE: Updated end to {event['end']['dateTime']}")
            
            if 'start_time' in event_data:
                start_time = event_data['start_time']
                logger.info(f"CALENDAR SERVICE: Updating start_time to {start_time}")
                if 'T' in str(start_time):
                    # ISO format datetime
                    event['start']['dateTime'] = start_time
                elif 'date' in event_data:
                    # Separate date and time
                    event['start']['dateTime'] = f"{event_data['date']}T{start_time}:00"
                else:
                    # Extract date from existing event start time or use today
                    existing_start = event.get('start', {}).get('dateTime', '')
                    if existing_start and 'T' in existing_start:
                        event_date = existing_start.split('T')[0]
                    else:
                        from datetime import datetime
                        event_date = datetime.now().strftime('%Y-%m-%d')
                    event['start']['dateTime'] = f"{event_date}T{start_time}:00"
            
            if 'end_time' in event_data:
                end_time = event_data['end_time']
                logger.info(f"CALENDAR SERVICE: Updating end_time to {end_time}")
                if 'T' in str(end_time):
                    # ISO format datetime
                    event['end']['dateTime'] = end_time
                elif 'date' in event_data:
                    # Separate date and time
                    event['end']['dateTime'] = f"{event_data['date']}T{end_time}:00"
                else:
                    # Extract date from existing event end time or use today
                    existing_end = event.get('end', {}).get('dateTime', '')
                    if existing_end and 'T' in existing_end:
                        event_date = existing_end.split('T')[0]
                    else:
                        from datetime import datetime
                        event_date = datetime.now().strftime('%Y-%m-%d')
                    event['end']['dateTime'] = f"{event_date}T{end_time}:00"
                
            logger.info(f"CALENDAR SERVICE: Final event object start={event.get('start', {}).get('dateTime', 'MISSING')}")
            logger.info(f"CALENDAR SERVICE: Final event object end={event.get('end', {}).get('dateTime', 'MISSING')}")
            logger.info(f"Updating event {event_id} with data: {event}")
            
            # If moving to a different calendar, delete from source and create in target
            if target_calendar_id != calendar_id:
                # Remove fields that shouldn't be copied
                event_copy = event.copy()
                for field in ['id', 'etag', 'created', 'updated', 'creator', 'organizer', 'iCalUID', 'sequence', 'eventType']:
                    event_copy.pop(field, None)
                
                # Create in target calendar
                new_event = self._handle_api_call(
                    lambda: service.events().insert(calendarId=target_calendar_id, body=event_copy).execute()
                )
                
                # Delete from source calendar
                self._handle_api_call(
                    lambda: service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
                )
                
                return {
                    'success': True,
                    'event_id': new_event['id'],
                    'event_link': new_event['htmlLink'],
                    'moved': True,
                    'from_calendar': calendar_id,
                    'to_calendar': target_calendar_id,
                    'updated_event': {
                        'summary': new_event.get('summary'),
                        'start': new_event.get('start', {}).get('dateTime', ''),
                        'end': new_event.get('end', {}).get('dateTime', ''),
                        'calendar_name': self.get_calendar_display_name(target_calendar_id),
                        'id': new_event.get('id'),
                        'htmlLink': new_event.get('htmlLink')
                    }
                }
            else:
                # Update in same calendar
                updated_event = self._handle_api_call(
                    lambda: service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
                )
                    
                return {
                    'success': True,
                    'event_id': updated_event['id'],
                    'event_link': updated_event['htmlLink'],
                    'updated_event': {
                        'summary': updated_event.get('summary'),
                        'start': updated_event.get('start', {}).get('dateTime', ''),
                        'end': updated_event.get('end', {}).get('dateTime', ''),
                        'calendar_name': self.get_calendar_display_name(target_calendar_id),
                        'id': updated_event.get('id'),
                        'htmlLink': updated_event.get('htmlLink')
                    }
                }
        except HTTPException:
            # Re-raise authentication errors
            raise
        except Exception as e:
            logger.error(f"Failed to update event: {e}")
            return {
                'success': False,
                'message': f'Failed to update event: {str(e)}'
            }
    
    def delete_event(self, event_id, calendar_id=None):
        """Delete an event from Google Calendar"""
        service = self.get_calendar_service()
        if not service:
            return {
                'success': False,
                'message': 'Authentication required',
                'auth_required': True
            }
        
        # Use provided calendar_id or default to primary
        calendar_to_use = calendar_id or 'primary'
        
        try:
            self._handle_api_call(
                lambda: service.events().delete(calendarId=calendar_to_use, eventId=event_id).execute()
            )
            return {'success': True, 'message': 'Event deleted successfully'}
        except HTTPException:
            # Re-raise authentication errors
            raise
        except Exception as e:
            logger.error(f"Failed to delete event: {e}")
            return {
                'success': False,
                'message': f'Failed to delete event: {str(e)}'
            }
    
    async def query_events(self, query_params):
        """Query events based on parameters, supporting multiple calendars"""
        try:
            service = self.get_calendar_service()
            if not service:
                logger.error("No authenticated Google Calendar service found.")
                return {
                    'success': False,
                    'message': 'Authentication required',
                    'auth_required': True
                }
            
            # Ensure calendars are loaded
            await self.ensure_calendars_loaded()
            
            # Initialize time bounds to None by default
            time_min = None
            time_max = None
            
            date_str = query_params.get('date')  
            if date_str:  
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    time_min = date_obj.isoformat()  # Start of day
                    time_max = date_obj.replace(hour=23, minute=59, second=59).isoformat()  # End of day
                except ValueError:
                    return {'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD'}

            # Determine which calendars to search
            calendar_ids = ['primary']  # Default to primary
            
            # If user specified a calendar, search only that one
            if 'calendar' in query_params or 'calendar_name' in query_params:
                specified_calendar = query_params.get('calendar') or query_params.get('calendar_name')
                calendar_id = self.calendar_agent._find_calendar_by_name(specified_calendar)
                if calendar_id:
                    calendar_ids = [calendar_id]
            else:
                # Search all calendars for better results - CRITICAL FIX
                # First ensure calendars are loaded and get fresh list
                try:
                    available_calendars_list = self.list_calendars()
                    if isinstance(available_calendars_list, list) and len(available_calendars_list) > 0:
                        # Extract calendar IDs from the list
                        calendar_ids = [cal.get('id', cal.get('calendar_id', 'primary')) for cal in available_calendars_list]
                        logger.info(f"🔍 CALENDAR FIX: Found {len(calendar_ids)} calendars to search")
                        logger.info(f"🔍 CALENDAR FIX: Calendar IDs: {calendar_ids}")
                    else:
                        # Fallback to cache if list_calendars fails
                        available_calendars = list(self.calendar_agent.calendar_cache.keys()) or ['primary']
                        calendar_ids = available_calendars
                        logger.warning(f"🔍 CALENDAR FIX: Fallback to cache - {len(calendar_ids)} calendars")
                except Exception as e:
                    logger.error(f"🔍 CALENDAR FIX: Error getting calendars, using primary only: {e}")
                    calendar_ids = ['primary']
                
                logger.info(f"🔍 CALENDAR DEBUG: Final search list - {len(calendar_ids)} calendars: {calendar_ids}")
                logger.info(f"🔍 CALENDAR DEBUG: Calendar cache size: {len(self.calendar_agent.calendar_cache)}")

            all_events = []
            
            # Query each calendar
            for calendar_id in calendar_ids:
                try:
                    # Fix variable scope by properly capturing variables in lambda
                    def make_query_call(cal_id, t_min, t_max):
                        # Build query parameters
                        query_kwargs = {
                            'calendarId': cal_id,
                            'timeMin': t_min if t_min else None,
                            'timeMax': t_max if t_max else None,
                            'singleEvents': True,
                            'orderBy': 'startTime'
                        }

                        # Add event name search if specified
                        event_name = query_params.get('event_name', '').strip()
                        if event_name:
                            query_kwargs['q'] = event_name

                        return lambda: service.events().list(**query_kwargs).execute()
                    
                    events_result = self._handle_api_call(
                        make_query_call(calendar_id, time_min, time_max)
                    )
                    
                    events = events_result.get('items', [])
                    calendar_info = self.calendar_agent.get_calendar_info(calendar_id)
                    calendar_name = calendar_info['name'] if calendar_info else calendar_id
                    
                    # Add calendar info to each event
                    for event in events:
                        event_data = {
                            'id': event['id'],
                            'summary': event.get('summary', 'No Title'),
                            'start': event['start'].get('dateTime', event['start'].get('date')),
                            'end': event['end'].get('dateTime', event['end'].get('date')),
                            'participants': event.get('attendees', []),
                            'description': event.get('description', ''),
                            'link': event.get('htmlLink', ''),
                            'calendar_name': calendar_name,
                            'calendar_id': calendar_id
                        }
                        all_events.append(event_data)
                        
                except Exception as e:
                    logger.warning(f"Failed to query calendar {calendar_id}: {e}")
                    continue
            
            if not all_events:
                # NO FALLBACK FUNCTIONALITY - per PROJECT_RULES.md
                # Return empty events list instead of hardcoded message
                return {'success': True, 'events': [], 'message': 'Query completed - no events found'}

            # Apply time filtering if specified
            if 'start_time_after' in query_params or 'start_time_before' in query_params:
                filtered_events = []
                start_time_after = query_params.get('start_time_after')
                start_time_before = query_params.get('start_time_before')
                
                for event in all_events:
                    event_start = event.get('start', '')
                    if not event_start:
                        continue
                    
                    try:
                        # Extract time from ISO datetime string (e.g., "2025-08-09T10:00:00+01:00" -> "10:00")
                        if 'T' in event_start:
                            time_part = event_start.split('T')[1].split('+')[0].split('-')[0]  # Handle timezone
                            event_time = time_part[:5]  # Get HH:MM format
                        else:
                            continue  # Skip all-day events
                        
                        # Apply time filters
                        skip_event = False
                        if start_time_after and event_time < start_time_after:
                            skip_event = True
                        if start_time_before and event_time > start_time_before:
                            skip_event = True
                        
                        if not skip_event:
                            filtered_events.append(event)
                    except Exception as e:
                        logger.warning(f"Error filtering event by time: {e}")
                        # Include event if time filtering fails
                        filtered_events.append(event)
                
                all_events = filtered_events

            # Sort all events by start time (baseline)
            all_events.sort(key=lambda x: x['start'])

            # Apply limit/order directives (Issue 1)
            limit = query_params.get('limit')
            order = (query_params.get('order') or '').lower()
            if order in ['desc', 'descending', 'reverse']:
                all_events = list(reversed(all_events))
            if isinstance(limit, int) and limit > 0:
                all_events = all_events[:limit]

            return {
                'success': True,
                'events': all_events,
                'calendars_searched': len(calendar_ids)
            }
        except HTTPException:
            # Re-raise authentication errors
            raise
        except Exception as e:
            logger.error(f"Exception in query_events: {e}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'message': f'Internal error: {e}'
            }

    def list_calendars(self):
        """Check if authentication works by listing calendars"""
        service = self.get_calendar_service()
        if not service:
            return "You are not authenticated. Please log in."

        try:
            calendars = self._handle_api_call(
                lambda: service.calendarList().list().execute()
            )
            return calendars.get("items", [])
        except HTTPException:
            # Re-raise authentication errors
            raise
        except Exception as e:
            logger.error(f"Error listing calendars: {e}")
            return f"Error listing calendars: {str(e)}"
