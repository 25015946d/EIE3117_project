from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User


class BearerTokenAuthentication(BaseAuthentication):
    keyword = 'Bearer'
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None
            
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Find user by stored token
        try:
            user = User.objects(auth_token=token).first()
            if user:
                return (user, token)
        except Exception:
            pass
            
        return None
    
    def authenticate_header(self, request):
        return 'Bearer'
