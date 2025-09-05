from django.urls import path
from . import views

urlpatterns = [
    path('google/', views.google_login, name='google_login'),
    path('callback/', views.google_callback, name='google_callback'),
    path('refresh/', views.refresh_token, name='refresh_token'),
    path('status/', views.auth_status, name='auth_status'),
    path('revoke/', views.revoke_access, name='revoke_access'),
    path('logout/', views.logout_view, name='logout'),
]