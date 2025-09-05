from rest_framework import serializers
from .models import CalendarEvent
from users.serializers import UserSerializer

class CalendarEventSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CalendarEvent
        fields = [
            'id', 'user', 'google_event_id', 'title', 'description',
            'start_datetime', 'end_datetime', 'location', 'is_all_day',
            'recurrence_rule', 'calendar_id', 'status', 'created_at',
            'updated_at', 'synced_with_google', 'last_synced_at'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at', 
            'synced_with_google', 'last_synced_at'
        ]

class CalendarEventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = [
            'title', 'description', 'start_datetime', 'end_datetime',
            'location', 'is_all_day', 'recurrence_rule', 'calendar_id'
        ]