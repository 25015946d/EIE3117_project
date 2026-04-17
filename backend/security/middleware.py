import time
import logging
from collections import defaultdict, deque
from django.http import HttpResponse
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('security')

class DDoSProtectionMiddleware:
    """Custom DDoS protection middleware for various attack types"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = defaultdict(lambda: deque(maxlen=1000))
        self.blocked_ips = defaultdict(int)
        
    def __call__(self, request):
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check if IP is blocked
        if self.is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return HttpResponse("Access Denied", status=403)
        
        # Rate limiting
        if self.is_rate_limited(client_ip):
            logger.warning(f"Rate limited request from: {client_ip}")
            return HttpResponse("Rate limit exceeded", status=429)
        
        # Slow HTTP attack protection
        if self.is_slow_http_attack(request):
            logger.warning(f"Slow HTTP attack detected from: {client_ip}")
            return HttpResponse("Request timeout", status=408)
        
        # Record request
        self.record_request(client_ip)
        
        response = self.get_response(request)
        
        # Add security headers
        self.add_security_headers(response)
        
        return response
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_ip_blocked(self, ip):
        """Check if IP is temporarily blocked"""
        block_key = f"blocked_{ip}"
        return cache.get(block_key, False)
    
    def block_ip(self, ip, duration=300):
        """Block IP for specified duration (seconds)"""
        block_key = f"blocked_{ip}"
        cache.set(block_key, True, duration)
        logger.warning(f"IP {ip} blocked for {duration} seconds")
    
    def is_rate_limited(self, ip):
        """Check if IP exceeds rate limits"""
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Get recent requests for this IP
        cache_key = f"requests_{ip}"
        requests = cache.get(cache_key, [])
        
        # Filter old requests
        recent_requests = [req_time for req_time in requests if req_time > window_start]
        
        # Check limits
        if len(recent_requests) > getattr(settings, 'RATE_LIMIT_REQUESTS_PER_MINUTE', 100):
            self.block_ip(ip, duration=300)  # Block for 5 minutes
            return True
        
        # Update cache
        recent_requests.append(current_time)
        cache.set(cache_key, recent_requests, 60)
        
        return False
    
    def is_slow_http_attack(self, request):
        """Detect slow HTTP attacks (Slowloris)"""
        # Check request processing time
        start_time = getattr(request, '_start_time', time.time())
        
        # If request is taking too long, it might be a slow attack
        if time.time() - start_time > getattr(settings, 'SLOW_HTTP_TIMEOUT', 30):
            return True
        
        # Check for incomplete headers
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length and int(content_length) > 0 and not request.body:
            return True
        
        return False
    
    def record_request(self, ip):
        """Record request for monitoring"""
        current_time = time.time()
        self.request_counts[ip].append(current_time)
        
        # Log suspicious patterns
        if len(self.request_counts[ip]) > 50:  # Many requests in short time
            logger.warning(f"High request volume from IP: {ip}")
    
    def add_security_headers(self, response):
        """Add security headers to response"""
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self'"
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'


class SQLInjectionProtectionMiddleware:
    """Protection against SQL and NoSQL injection attempts"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.suspicious_patterns = [
            r'(\bunion\b.*\bselect\b)',
            r'(\bor\b\s+\d+\s*=\s*\d+)',
            r'(\band\b\s+\d+\s*=\s*\d+)',
            r'(\bdrop\b\s+\btable\b)',
            r'(\bdelete\b\s+\bfrom\b)',
            r'(\binsert\b\s+\binto\b)',
            r'(\bupdate\b\s+\bset\b)',
            r'(\bexec\b\s*\()',
            r'(\bscript\b.*\balert\b)',
            r'(\bonload\b.*\balert\b)',
            r'(\bjavascript\b:)',
            r'(\bdocument\b\.\bcookie\b)',
            r'(\bwindow\b\.\blocation\b)',
        ]
    
    def __call__(self, request):
        # Check GET parameters
        for param, value in request.GET.items():
            if self.contains_suspicious_content(str(value)):
                logger.warning(f"Suspicious GET parameter detected: {param}={value}")
                return HttpResponse("Suspicious request detected", status=400)
        
        # Check POST data
        if hasattr(request, 'body') and request.body:
            try:
                import json
                if request.content_type == 'application/json':
                    data = json.loads(request.body.decode('utf-8'))
                    if self.check_dict_for_suspicious_content(data):
                        logger.warning(f"Suspicious POST data detected: {request.body}")
                        return HttpResponse("Suspicious request detected", status=400)
            except:
                pass
        
        return self.get_response(request)
    
    def contains_suspicious_content(self, content):
        """Check if content contains suspicious patterns"""
        import re
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def check_dict_for_suspicious_content(self, data):
        """Recursively check dictionary for suspicious content"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and self.contains_suspicious_content(value):
                    return True
                elif isinstance(value, (dict, list)):
                    if self.check_dict_for_suspicious_content(value):
                        return True
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str) and self.contains_suspicious_content(item):
                    return True
                elif isinstance(item, (dict, list)):
                    if self.check_dict_for_suspicious_content(item):
                        return True
        return False
