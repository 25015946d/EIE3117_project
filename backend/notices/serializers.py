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
        fields = ['id', 'responder', 'responder_nickname', 'responder_email', 'message', 'created_at']
        read_only_fields = ['id', 'responder', 'responder_nickname', 'responder_email', 'created_at']

    def get_responder_nickname(self, obj):
        user = obj.responder
        return user.nickname if user else 'Unknown'

    def get_responder_email(self, obj):
        user = obj.responder
        return user.email if user else 'Unknown'


class NoticeListSerializer(mongo_serializers.DocumentSerializer):
    responses_count = serializers.SerializerMethodField()
    owner_nickname = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = [
            'id', 'owner', 'owner_nickname', 'owner_email', 'title', 'type', 'date', 'venue', 'contact',
            'description', 'image', 'status', 'responses_count', 'created_at',
        ]
        read_only_fields = ['id', 'owner', 'status', 'created_at']

    def get_responses_count(self, obj):
        return Response.objects(notice=obj).count()

    def get_owner_nickname(self, obj):
        user = obj.owner
        return user.nickname if user else 'Unknown'

    def get_owner_email(self, obj):
        user = obj.owner
        return user.email if user else 'Unknown'


class NoticeDetailSerializer(mongo_serializers.DocumentSerializer):
    responses = ResponseSerializer(many=True, read_only=True)
    responses_count = serializers.SerializerMethodField()
    owner_nickname = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = [
            'id', 'owner', 'owner_nickname', 'owner_email',
            'title', 'type', 'date', 'venue', 'contact',
            'description', 'image', 'status',
            'responses', 'responses_count', 'created_at',
        ]
        read_only_fields = ['id', 'owner', 'status', 'created_at']

    def get_responses_count(self, obj):
        return Response.objects(notice=obj).count()

    def get_owner_nickname(self, obj):
        user = obj.owner
        return user.nickname if user else 'Unknown'

    def get_owner_email(self, obj):
        user = obj.owner
        return user.email if user else 'Unknown'
