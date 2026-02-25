from django.contrib.auth.backends import BaseBackend
from .models import User


class MongoDBAuthBackend(BaseBackend):
    """
    Custom authentication backend for MongoDB users
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user using MongoDB
        """
        email = kwargs.get('email') or username
        if not email or not password:
            return None
            
        try:
            user = User.objects.get(email=email.lower())
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        return None
    
    def get_user(self, user_id):
        """
        Retrieve user by user_id (not MongoDB _id)
        """
        try:
            return User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return None
