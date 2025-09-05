from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .services import AuthenticationService
import json

auth_service = AuthenticationService()

@api_view(['GET'])
@permission_classes([AllowAny])
def google_login(request):
    try:
        auth_url = auth_service.initiate_google_oauth(request)
        return Response({
            'auth_url': auth_url,
            'message': 'Redirect user to this URL to authenticate with Google'
        })
    except Exception as e:
        return Response({
            'error': f'Failed to initiate Google OAuth: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def google_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    if error:
        return Response({
            'error': f'Google OAuth error: {error}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not code or not state:
        return Response({
            'error': 'Missing code or state parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = auth_service.handle_google_callback(request, code, state)
        
        return Response({
            'message': 'Successfully authenticated with Google',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Authentication failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    try:
        success = auth_service.refresh_user_token(request.user)
        if success:
            return Response({'message': 'Token refreshed successfully'})
        else:
            return Response({
                'error': 'Failed to refresh token'
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Token refresh failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_status(request):
    is_authenticated = auth_service.is_user_authenticated_with_google(request.user)
    
    user_data = {
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'is_google_authenticated': is_authenticated
    }
    
    try:
        profile = request.user.profile
        user_data['google_email'] = profile.google_email
        user_data['token_expires_at'] = profile.token_expires_at
    except:
        pass
    
    return Response({
        'authenticated': True,
        'user': user_data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_access(request):
    try:
        success = auth_service.revoke_google_access(request.user)
        if success:
            return Response({'message': 'Google access revoked successfully'})
        else:
            return Response({
                'error': 'Failed to revoke access'
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Failed to revoke access: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        logout(request)
        return Response({'message': 'Logged out successfully'})
    except Exception as e:
        return Response({
            'error': f'Logout failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
