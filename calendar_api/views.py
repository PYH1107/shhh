from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from datetime import datetime, timedelta
from .models import CalendarEvent
from .services import GoogleCalendarService
from .serializers import CalendarEventSerializer, CalendarEventCreateSerializer
import json

class EventListCreateView(generics.ListCreateAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = CalendarEvent.objects.filter(user=user)
        
        start_date = self.request.query_params.get('start')
        end_date = self.request.query_params.get('end')
        
        if start_date:
            start_dt = parse_datetime(start_date)
            if start_dt:
                queryset = queryset.filter(start_datetime__gte=start_dt)
        
        if end_date:
            end_dt = parse_datetime(end_date)
            if end_dt:
                queryset = queryset.filter(start_datetime__lte=end_dt)
        
        return queryset.order_by('start_datetime')
    
    def perform_create(self, serializer):
        google_service = GoogleCalendarService()
        event = serializer.save(user=self.request.user)
        
        event_data = {
            'title': event.title,
            'description': event.description,
            'start_datetime': event.start_datetime,
            'end_datetime': event.end_datetime,
            'location': event.location,
            'is_all_day': event.is_all_day,
            'calendar_id': event.calendar_id,
        }
        
        google_event = google_service.create_event(self.request.user, event_data)
        if google_event:
            event.google_event_id = google_event['id']
            event.synced_with_google = True
            event.last_synced_at = timezone.now()
            event.save()

class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CalendarEvent.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        google_service = GoogleCalendarService()
        event = serializer.save()
        
        if event.google_event_id:
            event_data = {
                'title': event.title,
                'description': event.description,
                'start_datetime': event.start_datetime,
                'end_datetime': event.end_datetime,
                'location': event.location,
                'is_all_day': event.is_all_day,
            }
            
            google_event = google_service.update_event(
                self.request.user,
                event.google_event_id,
                event_data,
                event.calendar_id
            )
            if google_event:
                event.synced_with_google = True
                event.last_synced_at = timezone.now()
                event.save()
    
    def perform_destroy(self, instance):
        google_service = GoogleCalendarService()
        if instance.google_event_id:
            google_service.delete_event(
                self.request.user,
                instance.google_event_id,
                instance.calendar_id
            )
        instance.delete()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_calendars(request):
    try:
        google_service = GoogleCalendarService()
        service = google_service.get_calendar_service(request.user)
        
        if not service:
            return Response({
                'error': 'User not authenticated with Google'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        return Response({
            'calendars': calendars,
            'count': len(calendars)
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to list calendars: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_events(request):
    try:
        synced_events = google_service.sync_events_from_google(request.user)
        
        return Response({
            'message': f'Successfully synced {len(synced_events)} events from Google Calendar',
            'synced_count': len(synced_events)
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to sync events: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def google_events(request):
    try:
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')
        max_results = int(request.GET.get('max_results', 100))
        
        time_min = None
        time_max = None
        
        if start_date:
            time_min = start_date
        if end_date:
            time_max = end_date
        
        google_events = google_service.list_events(
            request.user,
            max_results=max_results,
            time_min=time_min,
            time_max=time_max
        )
        
        return Response({
            'google_events': google_events,
            'count': len(google_events)
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch Google events: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
