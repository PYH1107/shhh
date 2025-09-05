from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import UserProfileSerializer
from django.shortcuts import get_object_or_404

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile)
            return Response({
                'profile': serializer.data
            })
        except UserProfile.DoesNotExist:
            return Response({
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)

class UpdateUserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        try:
            user = request.user
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Update user fields
            user.first_name = request.data.get('first_name', user.first_name)
            user.last_name = request.data.get('last_name', user.last_name)
            user.email = request.data.get('email', user.email)
            user.save()
            
            # Update profile fields
            profile.google_email = request.data.get('google_email', profile.google_email)
            profile.save()
            
            serializer = UserProfileSerializer(profile)
            return Response({
                'message': 'Profile updated successfully',
                'profile': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to update profile: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
