from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response as DRFResponse
from datetime import datetime, date
from django.http import HttpResponse, Http404

from .models import Notice, Response
from .serializers import NoticeListSerializer, NoticeDetailSerializer, ResponseSerializer


@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def notice_list_create(request):
    if request.method == 'GET':
        notices = Notice.objects.all()
        serializer = NoticeListSerializer(notices, many=True, context={'request': request})
        return DRFResponse(serializer.data)

    # POST – must be authenticated
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return DRFResponse({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    token = auth_header[7:]
    try:
        from accounts.models import User
        user = User.objects(auth_token=token).first()
        if not user:
            return DRFResponse({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception:
        return DRFResponse({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    # Debug: Print request data
    print(f"Request data: {request.data}")
    print(f"Request FILES: {request.FILES}")
    print(f"Request content type: {request.content_type}")
    
    # Handle file upload - check both request.data and request.FILES
    if 'image' in request.FILES:
        print("Image found in request.FILES")
        request.data['image'] = request.FILES['image']
    elif 'image' in request.data:
        print("Image found in request.data")
    else:
        print("No image found in request")
    
    # Add user context to serializer
    request.current_user = user
    serializer = NoticeListSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        notice = serializer.save()
        print(f"Created notice: {notice}")
        print(f"Notice image: {notice.image}")
        return DRFResponse(serializer.data, status=status.HTTP_201_CREATED)
    else:
        print(f"Serializer errors: {serializer.errors}")
        return DRFResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def notice_detail(request, pk):
    try:
        notice = Notice.objects.get(pk=pk)
    except Notice.DoesNotExist:
        return DRFResponse({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = NoticeDetailSerializer(notice, context={'request': request})
    return DRFResponse(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
def my_notices(request):
    # Get user from token (similar to profile view)
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        try:
            from accounts.models import User
            user = User.objects(auth_token=token).first()
            if user:
                notices = Notice.objects.filter(owner_id=user.user_id)
                serializer = NoticeListSerializer(notices, many=True, context={'request': request})
                return DRFResponse(serializer.data)
        except Exception:
            pass
    
    return DRFResponse({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def respond_to_notice(request, pk):
    # Get user from token (similar to other views)
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return DRFResponse({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    token = auth_header[7:]
    try:
        from accounts.models import User
        user = User.objects(auth_token=token).first()
        if not user:
            return DRFResponse({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception:
        return DRFResponse({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        notice = Notice.objects.get(pk=pk)
    except Notice.DoesNotExist:
        return DRFResponse({'error': 'Notice not found.'}, status=status.HTTP_404_NOT_FOUND)

    if notice.status != 'active':
        return DRFResponse({'error': 'This notice is no longer active.'}, status=status.HTTP_400_BAD_REQUEST)

    # Allow all authenticated users to respond, including the notice owner
    # Remove the one-response limit - users can respond multiple times
    data = request.data.copy()

    serializer = ResponseSerializer(data=data)
    if serializer.is_valid():
        serializer.save(notice=notice, responder_id=user.user_id)
        return DRFResponse(serializer.data, status=status.HTTP_201_CREATED)
    return DRFResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def complete_notice(request, pk):
    # Get user from token (similar to other views)
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return DRFResponse({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    token = auth_header[7:]
    try:
        from accounts.models import User
        user = User.objects(auth_token=token).first()
        if not user:
            return DRFResponse({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception:
        return DRFResponse({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        notice = Notice.objects.get(pk=pk)
    except Notice.DoesNotExist:
        return DRFResponse({'error': 'Notice not found.'}, status=status.HTTP_404_NOT_FOUND)

    if notice.owner_id != user.user_id:
        return DRFResponse({'error': 'Only the owner can complete this notice.'}, status=status.HTTP_403_FORBIDDEN)

    if notice.status == 'completed':
        return DRFResponse({'error': 'Notice is already completed.'}, status=status.HTTP_400_BAD_REQUEST)

    notice.status = 'completed'
    notice.updated_at = datetime.now()
    notice.save()
    return DRFResponse(NoticeDetailSerializer(notice, context={'request': request}).data)


@api_view(['DELETE'])
def delete_notice(request, pk):
    # Get user from token (similar to other views)
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return DRFResponse({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    token = auth_header[7:]
    try:
        from accounts.models import User
        user = User.objects(auth_token=token).first()
        if not user:
            return DRFResponse({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception:
        return DRFResponse({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        notice = Notice.objects.get(pk=pk)
    except Notice.DoesNotExist:
        return DRFResponse({'error': 'Notice not found.'}, status=status.HTTP_404_NOT_FOUND)

    if notice.owner_id != user.user_id:
        return DRFResponse({'error': 'Only the owner can delete this notice.'}, status=status.HTTP_403_FORBIDDEN)

    notice.delete()
    return DRFResponse({'message': 'Notice deleted successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def serve_image(request, grid_id):
    """Serve images stored in GridFS"""
    try:
        from mongoengine import DoesNotExist
        from .models import Notice
        from bson import ObjectId
        
        print(f"Looking for image with grid_id: {grid_id}")
        
        # Convert grid_id to ObjectId
        try:
            grid_obj_id = ObjectId(grid_id)
        except:
            raise Http404("Invalid image ID")
        
        # Find all notices and check their images manually
        notices = Notice.objects.all()
        print(f"Total notices: {len(notices)}")
        
        for notice in notices:
            if notice.image:
                print(f"Notice {notice.id} has image: {notice.image}")
                if hasattr(notice.image, 'grid_id'):
                    print(f"Image grid_id: {notice.image.grid_id}")
                    if str(notice.image.grid_id) == grid_id:
                        print(f"Found matching image for notice {notice.id}")
                        
                        # Get the image data from GridFS
                        image_data = notice.image.read()
                        content_type = getattr(notice.image, 'content_type', 'image/jpeg')
                        
                        return HttpResponse(image_data, content_type=content_type)
        
        print("No matching image found")
        raise Http404("Image not found")
    except Exception as e:
        print(f"Error serving image: {e}")
        raise Http404("Image not found")
