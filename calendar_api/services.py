from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from .models import CalendarEvent
import json

class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, user=None):
        self.user = user
        
    def get_oauth_flow(self):
        flow = Flow.from_client_config({
            "web": {
                "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI]
            }
        }, scopes=self.SCOPES)
        flow.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
        return flow
    
    def get_authorization_url(self, state=None):
        flow = self.get_oauth_flow()
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )
        return auth_url
    
    def exchange_code_for_tokens(self, code):
        flow = self.get_oauth_flow()
        flow.fetch_token(code=code)
        return flow.credentials
    
    def get_credentials_from_user(self, user):
        try:
            google_token = user.google_token
            credentials = Credentials(
                token=google_token.access_token,
                refresh_token=google_token.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
                client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                scopes=self.SCOPES
            )
            return credentials
        except:
            return None
    
    def refresh_credentials(self, user):
        credentials = self.get_credentials_from_user(user)
        if credentials and credentials.expired:
            credentials.refresh()
            self.save_credentials_to_user(user, credentials)
        return credentials
    
    def save_credentials_to_user(self, user, credentials):
        from authentication.models import GoogleOAuthToken
        
        expires_at = timezone.now() + timedelta(seconds=credentials.expiry.timestamp() - timezone.now().timestamp())
        
        token, created = GoogleOAuthToken.objects.get_or_create(
            user=user,
            defaults={
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_type': 'Bearer',
                'expires_in': 3600,
                'expires_at': expires_at,
                'scope': ' '.join(self.SCOPES)
            }
        )
        
        if not created:
            token.access_token = credentials.token
            if credentials.refresh_token:
                token.refresh_token = credentials.refresh_token
            token.expires_at = expires_at
            token.save()
            
        return token
    
    def get_calendar_service(self, user):
        credentials = self.get_credentials_from_user(user)
        if not credentials:
            return None
            
        if credentials.expired:
            credentials = self.refresh_credentials(user)
            
        service = build('calendar', 'v3', credentials=credentials)
        return service
    
    def list_events(self, user, calendar_id='primary', max_results=100, time_min=None, time_max=None):
        service = self.get_calendar_service(user)
        if not service:
            return []
            
        if not time_min:
            time_min = timezone.now().isoformat()
        if not time_max:
            time_max = (timezone.now() + timedelta(days=30)).isoformat()
            
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    
    def create_event(self, user, event_data):
        service = self.get_calendar_service(user)
        if not service:
            return None
            
        event = service.events().insert(
            calendarId=event_data.get('calendar_id', 'primary'),
            body=self._format_event_for_google(event_data)
        ).execute()
        
        return event
    
    def update_event(self, user, event_id, event_data, calendar_id='primary'):
        service = self.get_calendar_service(user)
        if not service:
            return None
            
        event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=self._format_event_for_google(event_data)
        ).execute()
        
        return event
    
    def delete_event(self, user, event_id, calendar_id='primary'):
        service = self.get_calendar_service(user)
        if not service:
            return False
            
        try:
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            return True
        except:
            return False
    
    def _format_event_for_google(self, event_data):
        google_event = {
            'summary': event_data.get('title', ''),
            'description': event_data.get('description', ''),
            'location': event_data.get('location', ''),
        }
        
        if event_data.get('is_all_day', False):
            google_event['start'] = {
                'date': event_data['start_datetime'].date().isoformat(),
            }
            google_event['end'] = {
                'date': event_data['end_datetime'].date().isoformat(),
            }
        else:
            google_event['start'] = {
                'dateTime': event_data['start_datetime'].isoformat(),
                'timeZone': 'UTC',
            }
            google_event['end'] = {
                'dateTime': event_data['end_datetime'].isoformat(),
                'timeZone': 'UTC',
            }
        
        if event_data.get('recurrence_rule'):
            google_event['recurrence'] = [event_data['recurrence_rule']]
            
        return google_event
    
    def sync_events_from_google(self, user):
        google_events = self.list_events(user)
        synced_events = []
        
        for google_event in google_events:
            try:
                start_dt = self._parse_google_datetime(google_event['start'])
                end_dt = self._parse_google_datetime(google_event['end'])
                
                event, created = CalendarEvent.objects.update_or_create(
                    google_event_id=google_event['id'],
                    user=user,
                    defaults={
                        'title': google_event.get('summary', 'No Title'),
                        'description': google_event.get('description', ''),
                        'start_datetime': start_dt,
                        'end_datetime': end_dt,
                        'location': google_event.get('location', ''),
                        'is_all_day': 'date' in google_event['start'],
                        'status': google_event.get('status', 'confirmed'),
                        'synced_with_google': True,
                        'last_synced_at': timezone.now()
                    }
                )
                synced_events.append(event)
            except Exception as e:
                print(f"Error syncing event {google_event.get('id')}: {e}")
                continue
                
        return synced_events
    
    def _parse_google_datetime(self, datetime_obj):
        if 'dateTime' in datetime_obj:
            return datetime.fromisoformat(datetime_obj['dateTime'].replace('Z', '+00:00'))
        elif 'date' in datetime_obj:
            return datetime.fromisoformat(datetime_obj['date'] + 'T00:00:00+00:00')
        return timezone.now()