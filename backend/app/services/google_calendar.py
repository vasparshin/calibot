from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import os
import pickle
import traceback
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
    
    def get_auth_url(self):
        flow = Flow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRET_FILE,
            scopes=GOOGLE_API_SCOPES,
            redirect_uri=self.redirect_uri
        )
        print("Redirect URI:", flow.redirect_uri)
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        # Store only the state
        with open("oauth_state.txt", "w") as f:
            f.write(state)

        # store client_config and redirect_uri to use in the callback function.
        with open("client_config.pickle", "wb") as f:
            pickle.dump({"client_secrets_file": GOOGLE_CLIENT_SECRET_FILE, "scopes": GOOGLE_API_SCOPES, "redirect_uri": self.redirect_uri}, f)

        return auth_url

    async def handle_oauth_callback(self, request: Request):
        """Handle the OAuth callback and exchange code for token"""
        code = request.query_params.get('code')
        state = request.query_params.get('state')

        if not code or not state:
            logger.error("Missing code or state in OAuth callback")
            raise HTTPException(status_code=400, detail="Missing code or state")

        try:
            with open('oauth_state.txt', 'r') as f:
                saved_state = f.read()
            with open('client_config.pickle', 'rb') as f:
                client_config = pickle.load(f)

        except FileNotFoundError as e:
            logger.error(f"Authentication flow expired: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail="Authentication flow expired")

        if state != saved_state:
            logger.error("Invalid state parameter in OAuth callback")
            raise HTTPException(status_code=400, detail="Invalid state parameter")
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
                        <p>You can now close this tab.</p>
                    </div>
                </body>
                </html>
                """

            return HTMLResponse(content=html_content, status_code=200)

            # return {"message": "Authentication successful! Pllease close this tab."}
        except Exception as e:
            logger.error(f"Error during token exchange: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail="Failed to authenticate")

    def get_calendar_service(self):
        """Get an authenticated Google Calendar service."""
        if self.service:
            logger.info("✅ Using existing service instance.")
            return self.service

        # Load existing credentials if available
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    self.credentials = pickle.load(token)
            except Exception as e:
                logger.info(f"⚠️ Error loading credentials: {e}")
                if os.path.exists(self.token_path): 
                    os.remove(self.token_path)
                return None  # Force re-authentication

        # If credentials are valid, use them
        if self.credentials and self.credentials.valid:
            logger.info("✅ Loaded valid credentials.")
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return self.service

        # If credentials are expired but refreshable, refresh them
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                logger.info("🔄 Refreshing expired credentials...")
                self.credentials.refresh(GoogleRequest())
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.credentials, token)
                logger.info("✅ Credentials refreshed successfully.")
                self.service = build('calendar', 'v3', credentials=self.credentials)
                return self.service
            except Exception as e:
                logger.info(f"❌ Failed to refresh credentials: {e}")
                if os.path.exists(self.token_path):
                    os.remove(self.token_path)  # Remove invalid credentials
                return None

        # If no valid credentials are found, require authentication
        logger.info("⚠️ No valid credentials found. User must reauthenticate.")
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
            logger.info(f"⚠️ Failed to retrieve user time zone: {e}")
            return 'UTC'
    
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
                'dateTime': f"{event_data.get('date')}T{event_data.get('start_time')}:00",
                'timeZone': user_timezone,
            },
            'end': {
                'dateTime': f"{event_data.get('date')}T{event_data.get('end_time')}:00",
                'timeZone': user_timezone,
            },
        }
        
        # Add attendees if specified
        if event_data.get('participants'):
            event['attendees'] = [
                {'email': participant} for participant in event_data.get('participants')
                if '@' in participant  # Simple email validation
            ]
            
        # Get calendar name for logging
        calendar_info = self.calendar_agent.get_calendar_info(selected_calendar_id)
        calendar_name = calendar_info['name'] if calendar_info else selected_calendar_id
        
        logger.info(f"Creating event '{event['summary']}' in calendar '{calendar_name}' ({selected_calendar_id})")
        
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
    
    def update_event(self, event_id, event_data):
        """Update an existing event in Google Calendar"""
        service = self.get_calendar_service()
        if not service:
            return {
                'success': False,
                'message': 'Authentication required',
                'auth_required': True
            }
        try:
            # First retrieve the event
            event = self._handle_api_call(
                lambda: service.events().get(calendarId='primary', eventId=event_id).execute()
            )
            
            # Update fields
            if 'event_name' in event_data:
                event['summary'] = event_data['event_name']
            if 'description' in event_data:
                event['description'] = event_data['description']
            if 'date' in event_data and 'start_time' in event_data:
                event['start']['dateTime'] = f"{event_data['date']}T{event_data['start_time']}:00"
            if 'date' in event_data and 'end_time' in event_data:
                event['end']['dateTime'] = f"{event_data['date']}T{event_data['end_time']}:00"
                
            logger.info(f"Updating event {event_id} with data: {event}")
            updated_event = self._handle_api_call(
                lambda: service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
            )
                
            return {
                'success': True,
                'event_id': updated_event['id'],
                'event_link': updated_event['htmlLink']
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
    
    def delete_event(self, event_id):
        """Delete an event from Google Calendar"""
        service = self.get_calendar_service()
        if not service:
            return {
                'success': False,
                'message': 'Authentication required',
                'auth_required': True
            }
        try:
            self._handle_api_call(
                lambda: service.events().delete(calendarId='primary', eventId=event_id).execute()
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
                # Search all calendars for better results
                calendar_ids = list(self.calendar_agent.calendar_cache.keys()) or ['primary']

            all_events = []
            
            # Query each calendar
            for calendar_id in calendar_ids:
                try:
                    events_result = self._handle_api_call(
                        lambda: service.events().list(
                            calendarId=calendar_id,
                            timeMin=time_min if time_min else None,
                            timeMax=time_max if time_max else None,
                            singleEvents=True,
                            orderBy='startTime'
                        ).execute()
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
                return {'success': False, 'message': 'No matching events found'}

            # Sort all events by start time
            all_events.sort(key=lambda x: x['start'])

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
