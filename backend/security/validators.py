import re
import bleach
import logging
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger('security')

class SecurityValidator:
    """Enhanced input validation and sanitization"""
    
    # Malicious patterns to detect
    SQL_INJECTION_PATTERNS = [
        r'(\bunion\b.*\bselect\b)',
        r'(\bor\b\s+\d+\s*=\s*\d+)',
        r'(\band\b\s+\d+\s*=\s*\d+)',
        r'(\bdrop\b\s+\btable\b)',
        r'(\bdelete\b\s+\bfrom\b)',
        r'(\binsert\b\s+\binto\b)',
        r'(\bupdate\b\s+\bset\b)',
        r'(\bexec\b\s*\()',
        r'(\bexec\b\s*\w+)',
        r"(\bxp_cmdshell\b)",
        r"(\bsp_oacreate\b)",
    ]
    
    XSS_PATTERNS = [
        r'(<script[^>]*>.*?</script>)',
        r'(\bon\w+\s*=)',
        r'(\bjavascript\s*:)',
        r'(\bvbscript\s*:)',
        r'(\bdata\s*:)',
        r'(\bexpression\s*\()',
        r'(\balert\s*\()',
        r'(\bconfirm\s*\()',
        r'(\bprompt\s*\()',
        r'(\beval\s*\()',
        r'(\bsetTimeout\s*\()',
        r'(\bsetInterval\s*\()',
    ]
    
    NOSQL_INJECTION_PATTERNS = [
        r'(\{\s*\$ne\s*:)',
        r'(\{\s*\$gt\s*:)',
        r'(\{\s*\$lt\s*:)',
        r'(\{\s*\$in\s*:)',
        r'(\{\s*\$nin\s*:)',
        r'(\{\s*\$regex\s*:)',
        r'(\{\s*\$where\s*:)',
        r'(\{\s*\$exists\s*:)',
        r'(\{\s*\$or\s*:)',
        r'(\{\s*\$and\s*:)',
    ]
    
    @classmethod
    def validate_text_input(cls, value, field_name="input"):
        """Validate text input against various attacks"""
        if not value or not isinstance(value, str):
            return value
        
        # Check for SQL injection
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"SQL injection attempt detected in {field_name}: {value}")
                raise ValidationError(_('Potential SQL injection detected'))
        
        # Check for XSS
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"XSS attempt detected in {field_name}: {value}")
                raise ValidationError(_('Potential XSS detected'))
        
        # Check for NoSQL injection
        for pattern in cls.NOSQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"NoSQL injection attempt detected in {field_name}: {value}")
                raise ValidationError(_('Potential NoSQL injection detected'))
        
        return value
    
    @classmethod
    def sanitize_html(cls, value):
        """Sanitize HTML content to prevent XSS"""
        if not value or not isinstance(value, str):
            return value
        
        # Allowed HTML tags and attributes
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
        allowed_attributes = {}
        
        # Sanitize using bleach
        clean_value = bleach.clean(
            value,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
        
        return clean_value
    
    @classmethod
    def validate_email(cls, email):
        """Enhanced email validation"""
        if not email:
            return email
        
        # Basic email format check
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(_('Invalid email format'))
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'(\.\./)',
            r'(\.\.\\)',
            r'(\bunion\b)',
            r'(\bselect\b)',
            r'(\bdrop\b)',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                logger.warning(f"Suspicious email pattern detected: {email}")
                raise ValidationError(_('Invalid email format'))
        
        return email.lower()
    
    @classmethod
    def validate_username(cls, username):
        """Enhanced username validation"""
        if not username:
            return username
        
        # Username should only contain alphanumeric, underscore, and hyphen
        username_pattern = r'^[a-zA-Z0-9_-]{3,30}$'
        if not re.match(username_pattern, username):
            raise ValidationError(_('Username must be 3-30 characters and contain only letters, numbers, underscore, and hyphen'))
        
        # Check for reserved names
        reserved_names = ['admin', 'root', 'system', 'api', 'www', 'ftp', 'mail']
        if username.lower() in reserved_names:
            raise ValidationError(_('This username is reserved'))
        
        return username.lower()
    
    @classmethod
    def validate_notice_content(cls, title, description, venue, contact):
        """Validate notice content for security"""
        # Validate each field
        cls.validate_text_input(title, "title")
        cls.validate_text_input(description, "description")
        cls.validate_text_input(venue, "venue")
        cls.validate_text_input(contact, "contact")
        
        # Length validation
        if len(title) > 200:
            raise ValidationError(_('Title is too long'))
        if len(description) > 2000:
            raise ValidationError(_('Description is too long'))
        if len(venue) > 200:
            raise ValidationError(_('Venue is too long'))
        if len(contact) > 100:
            raise ValidationError(_('Contact information is too long'))
        
        return True
    
    @classmethod
    def validate_file_upload(cls, file_obj):
        """Validate uploaded files for security"""
        if not file_obj:
            return None
        
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if file_obj.size > max_size:
            raise ValidationError(_('File size must be less than 5MB'))
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        file_extension = file_obj.name.lower().split('.')[-1]
        
        if not any(file_obj.name.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError(_('Only image files are allowed'))
        
        # Check file content type
        allowed_mime_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if hasattr(file_obj, 'content_type') and file_obj.content_type not in allowed_mime_types:
            raise ValidationError(_('Invalid file type'))
        
        return file_obj

def validate_search_query(query):
    """Validate search queries to prevent injection attacks"""
    if not query:
        return query
    
    # Check for dangerous operators
    dangerous_patterns = [
        r'(\$ne)',
        r'(\$gt)',
        r'(\$lt)',
        r'(\$in)',
        r'(\$nin)',
        r'(\$regex)',
        r'(\$where)',
        r'(\$exists)',
        r'(\$or)',
        r'(\$and)',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            logger.warning(f"Dangerous MongoDB operator in search query: {query}")
            raise ValidationError(_('Invalid search query'))
    
    # Sanitize the query
    sanitized_query = bleach.clean(query, tags=[], strip=True)
    
    return sanitized_query[:100]  # Limit query length
