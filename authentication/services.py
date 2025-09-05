from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.utils import timezone
from datetime import timedelta
from calendar_api.services import GoogleCalendarService
from .models import GoogleOAuthToken
from users.models import UserProfile
import uuid

class AuthenticationService:
    
    def __init__(self):
        self.google_service = GoogleCalendarService()
    
    def initiate_google_oauth(self, request):
        state = str(uuid.uuid4())
        request.session['oauth_state'] = state
        
        auth_url = self.google_service.get_authorization_url(state=state)
        return auth_url
    
    def handle_google_callback(self, request, code, state):
        if request.session.get('oauth_state') != state:
            raise ValueError("Invalid state parameter")
        
        credentials = self.google_service.exchange_code_for_tokens(code)
        
        # Get user info from Google
        user_info = self._get_google_user_info(credentials)
        
        # Create or get user
        user = self._create_or_get_user(user_info)
        
        # Save credentials
        self.google_service.save_credentials_to_user(user, credentials)
        
        # Update user profile
        self._update_user_profile(user, user_info, credentials)
        
        # Authenticate user
        authenticate_user = authenticate(request, username=user.username)
        if authenticate_user:
            login(request, authenticate_user)
        
        return user
    
    def _get_google_user_info(self, credentials):
        from googleapiclient.discovery import build
        
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        
        return {
            'google_id': user_info.get('id'),
            'email': user_info.get('email'),
            'first_name': user_info.get('given_name', ''),
            'last_name': user_info.get('family_name', ''),
            'name': user_info.get('name', ''),
            'picture': user_info.get('picture', ''),
        }
    
    def _create_or_get_user(self, user_info):
        try:
            # Try to find user by Google ID first
            user_profile = UserProfile.objects.get(google_id=user_info['google_id'])
            user = user_profile.user
        except UserProfile.DoesNotExist:
            try:
                # Try to find user by email
                user = User.objects.get(email=user_info['email'])
            except User.DoesNotExist:
                # Create new user
                username = self._generate_username(user_info['email'])
                user = User.objects.create_user(
                    username=username,
                    email=user_info['email'],
                    first_name=user_info['first_name'],
                    last_name=user_info['last_name']
                )
        
        return user
    
    def _update_user_profile(self, user, user_info, credentials):
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        profile.google_id = user_info['google_id']
        profile.google_email = user_info['email']
        profile.google_access_token = credentials.token
        profile.google_refresh_token = credentials.refresh_token
        
        if credentials.expiry:
            profile.token_expires_at = credentials.expiry
        else:
            profile.token_expires_at = timezone.now() + timedelta(hours=1)
            
        profile.save()
        
        return profile
    
    def _generate_username(self, email):
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
            
        return username
    
    def refresh_user_token(self, user):
        try:
            google_service = GoogleCalendarService()
            credentials = google_service.refresh_credentials(user)
            
            if credentials:
                self._update_profile_tokens(user, credentials)
                return True
        except Exception as e:
            print(f"Error refreshing token for user {user.username}: {e}")
        
        return False
    
    def _update_profile_tokens(self, user, credentials):
        try:
            profile = user.profile
            profile.google_access_token = credentials.token
            if credentials.refresh_token:
                profile.google_refresh_token = credentials.refresh_token
            if credentials.expiry:
                profile.token_expires_at = credentials.expiry
            profile.save()
        except UserProfile.DoesNotExist:
            pass
    
    def is_user_authenticated_with_google(self, user):
        if not user.is_authenticated:
            return False
            
        try:
            google_token = user.google_token
            return not google_token.is_expired()
        except GoogleOAuthToken.DoesNotExist:
            return False
    
    def revoke_google_access(self, user):
        try:
            # Delete tokens
            GoogleOAuthToken.objects.filter(user=user).delete()
            
            # Clear profile tokens
            try:
                profile = user.profile
                profile.google_access_token = None
                profile.google_refresh_token = None
                profile.token_expires_at = None
                profile.save()
            except UserProfile.DoesNotExist:
                pass
                
            return True
        except Exception as e:
            print(f"Error revoking access for user {user.username}: {e}")
            return False