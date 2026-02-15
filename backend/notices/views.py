from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response as DRFResponse

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
    if not request.user or not request.user.is_authenticated:
        return DRFResponse({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = NoticeListSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(owner=request.user)
        return DRFResponse(serializer.data, status=status.HTTP_201_CREATED)
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
@permission_classes([IsAuthenticated])
def my_notices(request):
    notices = Notice.objects.filter(owner=request.user)
    serializer = NoticeListSerializer(notices, many=True, context={'request': request})
    return DRFResponse(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_to_notice(request, pk):
    try:
        notice = Notice.objects.get(pk=pk)
    except Notice.DoesNotExist:
        return DRFResponse({'error': 'Notice not found.'}, status=status.HTTP_404_NOT_FOUND)

    if notice.status != 'active':
        return DRFResponse({'error': 'This notice is no longer active.'}, status=status.HTTP_400_BAD_REQUEST)

    if notice.owner == request.user:
        return DRFResponse({'error': 'You cannot respond to your own notice.'}, status=status.HTTP_400_BAD_REQUEST)

    if Response.objects.filter(notice=notice, responder=request.user).exists():
        return DRFResponse({'error': 'You have already responded to this notice.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ResponseSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(notice=notice, responder=request.user)
        return DRFResponse(serializer.data, status=status.HTTP_201_CREATED)
    return DRFResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_notice(request, pk):
    try:
        notice = Notice.objects.get(pk=pk)
    except Notice.DoesNotExist:
        return DRFResponse({'error': 'Notice not found.'}, status=status.HTTP_404_NOT_FOUND)

    if notice.owner != request.user:
        return DRFResponse({'error': 'Only the owner can complete this notice.'}, status=status.HTTP_403_FORBIDDEN)

    if notice.status == 'completed':
        return DRFResponse({'error': 'Notice is already completed.'}, status=status.HTTP_400_BAD_REQUEST)

    notice.status = 'completed'
    notice.save()
    return DRFResponse(NoticeDetailSerializer(notice, context={'request': request}).data)
