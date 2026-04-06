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
        
        # Manual serialization since we switched from DocumentSerializer
        result = []
        for notice in notices:
            notice_data = {
                'id': str(notice.id),
                'owner_id': notice.owner_id,
                'title': notice.title,
                'type': notice.type,
                'date': notice.date,
                'venue': notice.venue,
                'contact': notice.contact,
                'description': notice.description,
                'status': notice.status,
                'created_at': notice.created_at,
                'responses_count': Response.objects(notice=notice).count(),
            }
            
            # Get owner info
            if notice.owner:
                notice_data['owner_nickname'] = notice.owner.nickname
                notice_data['owner_email'] = notice.owner.email
            else:
                notice_data['owner_nickname'] = 'Unknown'
                notice_data['owner_email'] = 'Unknown'
            
            # Get image URL
            if notice.image and hasattr(notice.image, 'grid_id'):
                notice_data['image_url'] = f'/notices/image/{notice.image.grid_id}/'
            else:
                notice_data['image_url'] = None
            
            result.append(notice_data)
        
        return DRFResponse(result)

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

    # Handle file upload - check both request.data and request.FILES
    # Create a mutable copy of the data without files
    from django.http import QueryDict
    data = QueryDict(mutable=True)
    
    # Copy all non-file data
    for key, value in request.data.items():
        if key != 'image':
            data[key] = value
    
    # Handle image file separately
    if 'image' in request.FILES:
        # Image found in request.FILES
        data['image'] = request.FILES['image']
    elif 'image' in request.data:
        # Image is already in request.data, no need to add it
        pass
    
    # Convert QueryDict to regular dict for serializer
    final_data = data.dict()
    if 'image' in request.FILES:
        final_data['image'] = request.FILES['image']
    
    # Add user context to serializer
    request.current_user = user
    serializer = NoticeListSerializer(data=final_data, context={'request': request})
    if serializer.is_valid():
        try:
            notice = serializer.save()
            # Re-serialize to get the correct image URL
            response_serializer = NoticeListSerializer(notice, context={'request': request})
            return DRFResponse(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Handle MongoEngine validation errors
            if hasattr(e, 'errors') or 'ValidationError' in str(type(e)):
                return DRFResponse({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return DRFResponse({'detail': 'Failed to create notice.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
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
    data['notice_id'] = str(notice.id)  # Pass the ID as string
    data['responder_id'] = user.user_id

    serializer = ResponseSerializer(data=data)
    if serializer.is_valid():
        response = serializer.save()
        return DRFResponse(ResponseSerializer(response).data, status=status.HTTP_201_CREATED)
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
        
        # Convert grid_id to ObjectId
        try:
            grid_obj_id = ObjectId(grid_id)
        except:
            return HttpResponse('Invalid image ID', status=404)
        
        # Find all notices and check their images manually
        notices = Notice.objects.all()
        
        for notice in notices:
            if notice.image and hasattr(notice.image, 'grid_id'):
                if str(notice.image.grid_id) == grid_id:
                    # Get the image data from GridFS
                    image_data = notice.image.read()
                    content_type = getattr(notice.image, 'content_type', 'image/jpeg')
                    
                    response = HttpResponse(image_data, content_type=content_type)
                    response['Content-Disposition'] = f'inline; filename="notice_{notice.id}_image.jpg"'
                    return response
        
        return HttpResponse('Image not found', status=404)
    except Exception as e:
        return HttpResponse(f'Error serving image: {str(e)}', status=500)
