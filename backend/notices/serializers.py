from rest_framework import serializers
from rest_framework_mongoengine import serializers as mongo_serializers
from .models import Notice, Response
from django.contrib.auth import get_user_model

User = get_user_model()


class ResponseSerializer(mongo_serializers.DocumentSerializer):
    responder_nickname = serializers.SerializerMethodField()
    responder_email = serializers.SerializerMethodField()

    class Meta:
        model = Response
        fields = ['id', 'responder_id', 'responder_nickname', 'responder_email', 'message', 'created_at']
        read_only_fields = ['id', 'responder_id', 'responder_nickname', 'responder_email', 'created_at']

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
        return super().create(validated_data)


class NoticeListSerializer(mongo_serializers.DocumentSerializer):
    responses_count = serializers.SerializerMethodField()
    owner_nickname = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = [
            'id', 'owner_id', 'owner_nickname', 'owner_email', 'title', 'type', 'date', 'venue', 'contact',
            'description', 'image', 'status', 'responses_count', 'created_at',
        ]
        read_only_fields = ['id', 'owner_id', 'status', 'created_at', 'updated_at']

    def get_responses_count(self, obj):
        return Response.objects(notice=obj).count()

    def get_owner_nickname(self, obj):
        user = obj.owner
        return user.nickname if user else 'Unknown'

    def get_owner_email(self, obj):
        user = obj.owner
        return user.email if user else 'Unknown'

    def get_image(self, obj):
        print(f"NoticeListSerializer get_image called for notice {obj.id}")
        print(f"obj.image: {obj.image}")
        if obj.image:
            print(f"obj.image type: {type(obj.image)}")
            if hasattr(obj.image, 'grid_id'):
                print(f"obj.image.grid_id: {obj.image.grid_id}")
                request = self.context.get('request')
                if request:
                    url = request.build_absolute_uri(f'/notices/image/{obj.image.grid_id}/')
                    print(f"Generated image URL: {url}")
                    return url
                url = f'/notices/image/{obj.image.grid_id}/'
                print(f"Generated image URL (no request): {url}")
                return url
        print("No image found, returning None")
        return None

    def create(self, validated_data):
        # Add required fields for MongoDB
        from datetime import datetime
        
        print(f"Serializer create called with validated_data: {validated_data}")
        
        # Handle image upload explicitly
        image_file = validated_data.pop('image', None)
        print(f"Extracted image_file: {image_file}")
        
        # Use MongoDB user_id instead of Django user.id
        current_user = getattr(self.context['request'], 'current_user', None)
        if current_user:
            validated_data['owner_id'] = current_user.user_id
        else:
            # Fallback for testing
            validated_data['owner_id'] = 'test_user_id'
        validated_data['created_at'] = datetime.now()
        validated_data['updated_at'] = datetime.now()
        
        # Create notice without image first
        notice = super().create(validated_data)
        print(f"Created notice without image: {notice.id}")
        
        # Handle image if provided
        if image_file:
            print(f"Processing image file: {image_file}")
            print(f"Image file name: {image_file.name}")
            print(f"Image file content type: {image_file.content_type}")
            print(f"Image file size: {image_file.size}")
            
            try:
                # Store image in GridFS
                notice.image.put(image_file, content_type=image_file.content_type)
                notice.save()
                print(f"Image stored with grid_id: {notice.image.grid_id}")
                print(f"Notice after image save: {notice.image}")
            except Exception as e:
                print(f"Error storing image: {e}")
                # Continue without image
                pass
        else:
            print("No image file to process")
        
        return notice


class NoticeDetailSerializer(mongo_serializers.DocumentSerializer):
    responses = serializers.SerializerMethodField()
    responses_count = serializers.SerializerMethodField()
    owner_nickname = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = [
            'id', 'owner_id', 'owner_nickname', 'owner_email',
            'title', 'type', 'date', 'venue', 'contact',
            'description', 'image', 'status',
            'responses', 'responses_count', 'created_at',
        ]
        read_only_fields = ['id', 'owner_id', 'status', 'created_at']

    def get_responses(self, obj):
        responses = Response.objects(notice=obj)
        return ResponseSerializer(responses, many=True).data

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
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/notices/image/{obj.image.grid_id}/')
            return f'/notices/image/{obj.image.grid_id}/'
        return None
