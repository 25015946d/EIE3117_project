from rest_framework import serializers
from .models import Notice, Response
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from PIL import Image
import os

User = get_user_model()


def process_image(image_file, max_size_mb=5, max_width=1200, max_height=1200, max_compressed_mb=2):
    """
    Process uploaded image:
    - Allow larger initial files (up to 5MB)
    - Resize and compress to reduce file size
    - Validate final compressed size (max 2MB)
    """
    # Check initial file size (allow larger files for processing)
    max_initial_size = max_size_mb * 1024 * 1024
    
    if image_file.size > max_initial_size:
        raise serializers.ValidationError(f"Image size must be less than {max_size_mb}MB")
    
    try:
        # Open image with PIL
        img = Image.open(image_file)
        
        # Convert to RGB if necessary (for JPEG compression)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize if image is too large
        if img.width > max_width or img.height > max_height:
            # Calculate new dimensions maintaining aspect ratio
            ratio = min(max_width / img.width, max_height / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Compress image
        output = BytesIO()
        
        # Determine format and quality
        if image_file.content_type == 'image/png':
            img.save(output, format='PNG', optimize=True)
        else:
            # Default to JPEG for better compression
            img.save(output, format='JPEG', quality=85, optimize=True)
        
        output.seek(0)
        
        # Check compressed file size
        compressed_size = output.tell()
        max_compressed_bytes = max_compressed_mb * 1024 * 1024
        
        if compressed_size > max_compressed_bytes:
            # Try more aggressive compression
            output = BytesIO()
            img.save(output, format='JPEG', quality=70, optimize=True)
            output.seek(0)
            compressed_size = output.tell()
            
            if compressed_size > max_compressed_bytes:
                raise serializers.ValidationError(f"Image too large after compression. Maximum allowed size is {max_compressed_mb}MB")
        
        # Create new InMemoryUploadedFile
        new_filename = os.path.splitext(image_file.name)[0] + '.jpg'
        processed_file = InMemoryUploadedFile(
            output,
            'image',
            new_filename,
            'image/jpeg',
            output.tell(),
            None
        )
        
        return processed_file
        
    except Exception as e:
        raise serializers.ValidationError(f"Error processing image: {str(e)}")


class ResponseSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    notice_id = serializers.CharField(write_only=True)
    responder_id = serializers.CharField(write_only=True)
    responder_nickname = serializers.SerializerMethodField()
    responder_email = serializers.SerializerMethodField()
    message = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)

    def __init__(self, *args, **kwargs):
        self.many = kwargs.pop('many', False)
        super().__init__(*args, **kwargs)

    def get_responder_nickname(self, obj):
        user = obj.responder
        return user.nickname if user else 'Unknown'

    def get_responder_email(self, obj):
        user = obj.responder
        return user.email if user else 'Unknown'

    def create(self, validated_data):
        # Add required fields for MongoDB
        from datetime import datetime
        validated_data['created_at'] = datetime.now()
        
        # Extract notice_id and responder_id from validated_data
        notice_id = validated_data.pop('notice_id', None)
        responder_id = validated_data.pop('responder_id', None)
        
        # Get the notice object
        try:
            notice = Notice.objects.get(id=notice_id)
        except Notice.DoesNotExist:
            raise serializers.ValidationError(f"Notice with id {notice_id} not found")
        
        # Create the Response object manually
        response = Response(
            message=validated_data['message'],
            created_at=validated_data['created_at']
        )
        
        # Set the notice and responder_id as attributes
        response.notice = notice
        if responder_id:
            response.responder_id = responder_id
            
        response.save()
        return response


class NoticeListSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    owner_id = serializers.CharField(read_only=True)
    owner_nickname = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    title = serializers.CharField()
    type = serializers.CharField()
    date = serializers.DateField()
    venue = serializers.CharField()
    contact = serializers.CharField()
    description = serializers.CharField()
    image = serializers.ImageField(required=False, allow_null=True, write_only=True, 
                                   error_messages={
                                       'invalid_image': 'Upload a valid image file.',
                                       'invalid': 'Please upload a valid image file (JPEG, PNG, etc).'
                                   })
    image_url = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    responses_count = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    def __init__(self, *args, **kwargs):
        self.many = kwargs.pop('many', False)
        super().__init__(*args, **kwargs)

    def get_responses_count(self, obj):
        return Response.objects(notice=obj).count()

    def get_owner_nickname(self, obj):
        user = obj.owner
        return user.nickname if user else 'Unknown'

    def get_owner_email(self, obj):
        user = obj.owner
        return user.email if user else 'Unknown'

    def get_image_url(self, obj):
        """Generate image URL for frontend"""
        if obj.image and hasattr(obj.image, 'grid_id'):
            # Return relative URL to work with proxy
            return f'/notices/image/{obj.image.grid_id}/'
        return None

    def create(self, validated_data):
        # Add required fields for MongoDB
        from datetime import datetime
        
        # Handle image upload explicitly
        image_file = validated_data.pop('image', None)
        
        # Use MongoDB user_id instead of Django user.id
        current_user = getattr(self.context['request'], 'current_user', None)
        if current_user:
            owner_id = current_user.user_id
        else:
            # Fallback for testing
            owner_id = 'test_user_id'
        
        # Create notice without image first
        notice = Notice(
            title=validated_data['title'],
            type=validated_data['type'],
            date=validated_data['date'],
            venue=validated_data['venue'],
            contact=validated_data['contact'],
            description=validated_data['description'],
            owner_id=owner_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        notice.save()
        
        # Handle image if provided
        if image_file:
            try:
                # Process image (resize and compress)
                processed_image = process_image(image_file)
                
                # Store processed image in GridFS
                notice.image.put(processed_image, content_type='image/jpeg')
                notice.save()
            except serializers.ValidationError as e:
                # Re-raise validation errors
                raise e
            except Exception as e:
                # Continue without image if storage fails
                pass
        
        return notice


class NoticeDetailSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    owner_id = serializers.CharField(read_only=True)
    owner_nickname = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    title = serializers.CharField()
    type = serializers.CharField()
    date = serializers.DateField()
    venue = serializers.CharField()
    contact = serializers.CharField()
    description = serializers.CharField()
    image = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    responses = serializers.SerializerMethodField()
    responses_count = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    def get_responses(self, obj):
        responses = Response.objects(notice=obj)
        result = []
        for response in responses:
            response_data = {
                'id': str(response.id),
                'message': response.message,
                'created_at': response.created_at,
            }
            
            # Get responder info
            if response.responder:
                response_data['responder_nickname'] = response.responder.nickname
                response_data['responder_email'] = response.responder.email
            else:
                response_data['responder_nickname'] = 'Unknown'
                response_data['responder_email'] = 'Unknown'
            
            result.append(response_data)
        return result

    def get_responses_count(self, obj):
        return Response.objects(notice=obj).count()

    def get_owner_nickname(self, obj):
        user = obj.owner
        return user.nickname if user else 'Unknown'

    def get_owner_email(self, obj):
        user = obj.owner
        return user.email if user else 'Unknown'

    def get_image(self, obj):
        if obj.image and hasattr(obj.image, 'grid_id'):
            # Return relative URL to work with proxy
            return f'/notices/image/{obj.image.grid_id}/'
        return None
