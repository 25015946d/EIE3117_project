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
    image = serializers.ImageField(required=False, allow_null=True, write_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = [
            'id', 'owner_id', 'owner_nickname', 'owner_email', 'title', 'type', 'date', 'venue', 'contact',
            'description', 'image', 'image_url', 'status', 'responses_count', 'created_at',
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

    def get_image_url(self, obj):
        """Generate image URL for frontend"""
        if obj.image and hasattr(obj.image, 'grid_id'):
            # Return relative URL to work with proxy
            return f'/notices/image/{obj.image.grid_id}/'
        return None

    def create(self, validated_data):
        # Add required fields for MongoDB
        from datetime import datetime
        
        print(f"DEBUG: Serializer create called with validated_data keys: {list(validated_data.keys())}")
        
        # Handle image upload explicitly
        image_file = validated_data.pop('image', None)
        print(f"DEBUG: Extracted image_file: {image_file}")
        if image_file:
            print(f"DEBUG: Image file type: {type(image_file)}")
        
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
        print(f"DEBUG: Created notice: {notice.id}")
        
        # Handle image if provided
        if image_file:
            print(f"DEBUG: Processing image file...")
            try:
                # Store image in GridFS
                notice.image.put(image_file, content_type=getattr(image_file, 'content_type', 'image/jpeg'))
                notice.save()
                print(f"DEBUG: Image stored successfully")
                if hasattr(notice.image, 'grid_id'):
                    print(f"DEBUG: Grid ID: {notice.image.grid_id}")
            except Exception as e:
                print(f"DEBUG: Error storing image: {e}")
                import traceback
                traceback.print_exc()
                # Continue without image if storage fails
                pass
        else:
            print("DEBUG: No image file to process")
        
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
            # Return relative URL to work with proxy
            return f'/notices/image/{obj.image.grid_id}/'
        return None
