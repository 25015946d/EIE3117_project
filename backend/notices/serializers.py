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
        if obj.image and hasattr(obj.image, 'grid_id'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/notices/image/{obj.image.grid_id}/')
            return f'/notices/image/{obj.image.grid_id}/'
        return None

    def create(self, validated_data):
        # Add required fields for MongoDB
        from datetime import datetime
        validated_data['owner_id'] = self.context['request'].user.id
        validated_data['created_at'] = datetime.now()
        validated_data['updated_at'] = datetime.now()
        return super().create(validated_data)


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
