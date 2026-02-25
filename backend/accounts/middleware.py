from django.utils.deprecation import MiddlewareMixin
from rest_framework.authtoken.models import Token
from .models import User


class MongoDBAuthMiddleware(MiddlewareMixin):
    """
    Middleware to attach MongoDB user to request object
    """
    
    def process_request(self, request):
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token_key = auth_header[7:]  # Remove 'Bearer ' prefix
            
            try:
                token = Token.objects.get(key=token_key)
                # Get MongoDB user using the hashed user_id from token
                import hashlib
                # Reverse the hash lookup by finding user with matching hash
                users = User.objects.all()
                for user in users:
                    user_hash = int(hashlib.md5(user.user_id.encode()).hexdigest()[:8], 16)
                    if user_hash == token.user_id:
                        request.current_user = user
                        request.current_user_id = user.user_id
                        break
                else:
                    request.current_user = None
                    request.current_user_id = None
            except Token.DoesNotExist:
                request.current_user = None
                request.current_user_id = None
        else:
            request.current_user = None
            request.current_user_id = None
