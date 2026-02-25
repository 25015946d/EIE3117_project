from django.conf import settings
from django.db import models
from mongoengine import Document, StringField, DateTimeField, DateField, ReferenceField, CASCADE, IntField, ImageField


class Notice(Document):
    TYPE_CHOICES = [
        ('lost', 'Lost'),
        ('found', 'Found'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    owner_id = StringField(required=True)  # Reference to MongoDB User user_id
    title = StringField(required=True, max_length=255)
    type = StringField(required=True, choices=TYPE_CHOICES, max_length=10)
    date = DateField(required=True)
    venue = StringField(required=True, max_length=255)
    contact = StringField(required=True, max_length=255)
    description = StringField(required=True)
    image = ImageField()
    status = StringField(choices=STATUS_CHOICES, default='active', max_length=20)
    created_at = DateTimeField(required=True)
    updated_at = DateTimeField(required=True)

    meta = {
        'ordering': ['-created_at'],
        'collection': 'notices'
    }

    def __str__(self):
        return f'[{self.type}] {self.title}'

    @property
    def owner(self):
        """Get MongoDB User object from owner_id"""
        try:
            from accounts.models import User
            return User.objects.get(user_id=str(self.owner_id))
        except:
            return None


class Response(Document):
    notice = ReferenceField(Notice, reverse_delete_schema=CASCADE)
    responder_id = StringField(required=True)  # Reference to MongoDB User user_id
    message = StringField(required=True)
    created_at = DateTimeField(required=True)

    meta = {
        'ordering': ['-created_at'],
        'collection': 'responses'
    }

    def __str__(self):
        return f'Response by user {self.responder_id} on {self.notice}'

    @property
    def responder(self):
        """Get MongoDB User object from responder_id"""
        try:
            from accounts.models import User
            return User.objects.get(user_id=self.responder_id)
        except:
            return None
