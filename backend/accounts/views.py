from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.core.files.base import ContentFile
import base64

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, ProfileUpdateSerializer, ProfileSerializer
from .models import User, Profile
from .auth_backends import MongoDBAuthBackend


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Generate a simple token and store it in the user document
        import secrets
        token_key = secrets.token_urlsafe(32)
        user.auth_token = token_key
        user.save()
        
        return Response({
            'token': token_key,
            'user': UserSerializer(user, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = authenticate(
            request,
            username=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {'non_field_errors': ['Invalid email or password.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Generate a simple token and store it in the user document
        import secrets
        token_key = secrets.token_urlsafe(32)
        user.auth_token = token_key
        user.save()
        
        return Response({
            'token': token_key,
            'user': UserSerializer(user, context={'request': request}).data,
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
@parser_classes([MultiPartParser, FormParser, JSONParser])
def profile_view(request):
    # For testing, get the user with the token from Authorization header
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        user = User.objects(auth_token=token).first()
        if user:
            if request.method == 'GET':
                return Response(UserSerializer(user, context={'request': request}).data)
            
            serializer = ProfileUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                updated_user = serializer.save()
                return Response(UserSerializer(updated_user, context={'request': request}).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'error': 'Invalid or missing token'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_detail_view(request):
    """Get detailed profile information including completion percentage"""
    try:
        profile = Profile.objects(user=request.user).first()
        if not profile:
            # Create profile if it doesn't exist
            profile = Profile.objects.create(user=request.user)
        
        completion_percentage = profile.calculate_completion_percentage()
        
        return Response({
            'profile': ProfileSerializer(profile).data,
            'completion_percentage': completion_percentage,
            'profile_complete': profile.profile_complete
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({'detail': 'Logged out.'})


@api_view(['GET'])
@permission_classes([AllowAny])
def profile_image_view(request, user_id):
    """Serve profile image for a user"""
    try:
        user = User.objects.get(user_id=user_id)
        if user.profile_image:
            # Serve the image from MongoDB GridFS
            response = HttpResponse(user.profile_image.read(), content_type='image/jpeg')
            response['Content-Disposition'] = f'inline; filename="{user.username}_profile.jpg"'
            return response
        else:
            # Return a default profile image or 404
            return HttpResponse('Profile image not found', status=404)
    except User.DoesNotExist:
        return HttpResponse('User not found', status=404)
    except Exception as e:
        return HttpResponse(f'Error serving image: {str(e)}', status=500)
