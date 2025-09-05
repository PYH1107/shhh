from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CalendarEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    google_event_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    is_all_day = models.BooleanField(default=False)
    recurrence_rule = models.TextField(blank=True, null=True)
    calendar_id = models.CharField(max_length=255, default='primary')
    status = models.CharField(max_length=50, default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    synced_with_google = models.BooleanField(default=False)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['start_datetime']
        
    def __str__(self):
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        if self.pk and self.synced_with_google:
            self.last_synced_at = timezone.now()
        super().save(*args, **kwargs)
