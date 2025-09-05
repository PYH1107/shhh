from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.EventListCreateView.as_view(), name='event_list_create'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('sync/', views.sync_events, name='sync_events'),
    path('calendars/', views.list_calendars, name='list_calendars'),
]