from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from datetime import datetime, timedelta
from .models import CalendarEvent
from .services import GoogleCalendarService
from .serializers import CalendarEventSerializer
import json

google_service = GoogleCalendarService()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_events(request):
    try:
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')
        max_results = int(request.GET.get('max_results', 100))
        
        time_min = None
        time_max = None
        
        if start_date:
            time_min = parse_datetime(start_date)
        if end_date:
            time_max = parse_datetime(end_date)
            
        if not time_min:
            time_min = timezone.now()
        if not time_max:
            time_max = time_min + timedelta(days=30)
        
        events = CalendarEvent.objects.filter(
            user=request.user,
            start_datetime__gte=time_min,
            start_datetime__lte=time_max
        )[:max_results]
        
        serializer = CalendarEventSerializer(events, many=True)
        
        return Response({
            'events': serializer.data,
            'count': events.count()
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to list events: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_event(request):
    try:
        data = request.data
        
        event_data = {
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'start_datetime': parse_datetime(data.get('start_datetime')),
            'end_datetime': parse_datetime(data.get('end_datetime')),
            'location': data.get('location', ''),
            'is_all_day': data.get('is_all_day', False),
            'calendar_id': data.get('calendar_id', 'primary'),
        }
        
        local_event = CalendarEvent.objects.create(
            user=request.user,
            **event_data
        )
        
        google_event = google_service.create_event(request.user, event_data)
        
        if google_event:
            local_event.google_event_id = google_event['id']
            local_event.synced_with_google = True
            local_event.last_synced_at = timezone.now()
            local_event.save()
        
        serializer = CalendarEventSerializer(local_event)
        
        return Response({
            'message': 'Event created successfully',
            'event': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to create event: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def event_detail(request, event_id):
    try:
        event = CalendarEvent.objects.get(id=event_id, user=request.user)
    except CalendarEvent.DoesNotExist:
        return Response({
            'error': 'Event not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = CalendarEventSerializer(event)
        return Response({'event': serializer.data})
    
    elif request.method == 'PUT':
        try:
            data = request.data
            
            event.title = data.get('title', event.title)
            event.description = data.get('description', event.description)
            if data.get('start_datetime'):
                event.start_datetime = parse_datetime(data.get('start_datetime'))
            if data.get('end_datetime'):
                event.end_datetime = parse_datetime(data.get('end_datetime'))
            event.location = data.get('location', event.location)
            event.is_all_day = data.get('is_all_day', event.is_all_day)
            
            event_data = {
                'title': event.title,
                'description': event.description,
                'start_datetime': event.start_datetime,
                'end_datetime': event.end_datetime,
                'location': event.location,
                'is_all_day': event.is_all_day,
            }
            
            if event.google_event_id:
                google_event = google_service.update_event(
                    request.user, 
                    event.google_event_id, 
                    event_data,
                    event.calendar_id
                )
                if google_event:
                    event.synced_with_google = True
                    event.last_synced_at = timezone.now()
            
            event.save()
            
            serializer = CalendarEventSerializer(event)
            return Response({
                'message': 'Event updated successfully',
                'event': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to update event: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            if event.google_event_id:
                google_service.delete_event(
                    request.user, 
                    event.google_event_id, 
                    event.calendar_id
                )
            
            event.delete()
            
            return Response({
                'message': 'Event deleted successfully'
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to delete event: {str(e)}'
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
