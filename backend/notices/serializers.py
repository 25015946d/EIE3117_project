from rest_framework import serializers
from .models import Notice, Response


class ResponseSerializer(serializers.ModelSerializer):
    responder_nickname = serializers.CharField(source='responder.nickname', read_only=True)
    responder_email = serializers.CharField(source='responder.email', read_only=True)

    class Meta:
        model = Response
        fields = ['id', 'responder', 'responder_nickname', 'responder_email', 'message', 'created_at']
        read_only_fields = ['id', 'responder', 'responder_nickname', 'responder_email', 'created_at']


class NoticeListSerializer(serializers.ModelSerializer):
    responses_count = serializers.IntegerField(source='responses.count', read_only=True)
    owner_nickname = serializers.CharField(source='owner.nickname', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)

    class Meta:
        model = Notice
        fields = [
            'id', 'owner', 'owner_nickname', 'owner_email', 'title', 'type', 'date', 'venue', 'contact',
            'description', 'image', 'status', 'responses_count', 'created_at',
        ]
        read_only_fields = ['id', 'owner', 'status', 'created_at']


class NoticeDetailSerializer(serializers.ModelSerializer):
    responses = ResponseSerializer(many=True, read_only=True)
    responses_count = serializers.IntegerField(source='responses.count', read_only=True)
    owner_nickname = serializers.CharField(source='owner.nickname', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)

    class Meta:
        model = Notice
        fields = [
            'id', 'owner', 'owner_nickname', 'owner_email',
            'title', 'type', 'date', 'venue', 'contact',
            'description', 'image', 'status',
            'responses', 'responses_count', 'created_at',
        ]
        read_only_fields = ['id', 'owner', 'status', 'created_at']
