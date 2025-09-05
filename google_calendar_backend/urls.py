"""
URL configuration for google_calendar_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import render

@require_GET
def api_info(request):
    return JsonResponse({
        'message': 'Google Calendar Backend API',
        'version': '1.0.0',
        'endpoints': {
            'authentication': {
                'google_login': '/auth/google/',
                'callback': '/auth/callback/',
                'status': '/auth/status/',
                'refresh': '/auth/refresh/',
                'logout': '/auth/logout/',
                'revoke': '/auth/revoke/'
            },
            'calendar': {
                'events': '/api/events/',
                'event_detail': '/api/events/<id>/',
                'sync_events': '/api/sync/',
                'calendars': '/api/calendars/'
            },
            'users': {
                'profile': '/users/profile/',
                'update_profile': '/users/profile/update/'
            },
            'admin': '/admin/'
        },
        'documentation': {
            'authentication_flow': 'Start with /auth/google/ to get OAuth URL',
            'note': 'Most endpoints require authentication'
        }
    })

@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
@csrf_exempt
def cors_test(request):
    """CORS test endpoint for frontend developers"""
    return Response({
        'method': request.method,
        'cors_enabled': True,
        'headers': dict(request.headers),
        'message': 'CORS is working correctly!'
    })

def login_page(request):
    """Simple login page for testing"""
    return render(request, 'login.html')

urlpatterns = [
    path('', api_info, name='api_info'),
    path('login/', login_page, name='login_page'),
    path('cors-test/', cors_test, name='cors_test'),
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls')),
    path('api/', include('calendar_api.urls')),
    path('users/', include('users.urls')),
]
