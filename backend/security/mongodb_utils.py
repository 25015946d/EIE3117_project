import logging
import re
from mongoengine import Q
from django.core.exceptions import ValidationError
from security.validators import validate_search_query

logger = logging.getLogger('security')

class SecureMongoDBQuery:
    """Secure MongoDB query builder to prevent NoSQL injection"""
    
    @staticmethod
    def build_search_query(search_term=None, notice_type=None, status=None):
        """Build secure search query for notices"""
        query = Q()
        
        # Secure search term handling
        if search_term:
            try:
                # Validate and sanitize search term
                clean_search = validate_search_query(search_term)
                
                # Build secure search query using exact matches and regex
                search_conditions = []
                
                # Only allow alphanumeric, spaces, and basic punctuation in search
                if re.match(r'^[a-zA-Z0-9\s\-_.,]+$', clean_search):
                    search_conditions.append(Q(title__icontains=clean_search))
                    search_conditions.append(Q(description__icontains=clean_search))
                    search_conditions.append(Q(venue__icontains=clean_search))
                    
                    # Combine with OR
                    if search_conditions:
                        query = query & (search_conditions[0] | search_conditions[1] | search_conditions[2])
                else:
                    logger.warning(f"Invalid search term pattern: {search_term}")
                    
            except ValidationError:
                logger.warning(f"Search validation failed for: {search_term}")
                # Return empty query if validation fails
                return Q(pk__in=[])  # Empty result set
        
        # Secure notice type filtering
        if notice_type:
            allowed_types = ['lost', 'found']
            if notice_type.lower() in allowed_types:
                query = query & Q(type__exact=notice_type.lower())
            else:
                logger.warning(f"Invalid notice type attempted: {notice_type}")
                return Q(pk__in=[])  # Empty result set
        
        # Secure status filtering
        if status:
            allowed_statuses = ['active', 'completed']
            if status.lower() in allowed_statuses:
                query = query & Q(status__exact=status.lower())
            else:
                logger.warning(f"Invalid status attempted: {status}")
                return Q(pk__in=[])  # Empty result set
        
        return query
    
    @staticmethod
    def secure_user_lookup(user_id):
        """Secure user lookup to prevent injection"""
        try:
            # Validate user_id format (should be a valid ObjectId or string)
            if not user_id or not isinstance(user_id, str):
                return None
            
            # Only allow alphanumeric, hyphens, and underscores for user lookups
            if not re.match(r'^[a-zA-Z0-9\-_]+$', user_id):
                logger.warning(f"Invalid user_id format: {user_id}")
                return None
            
            from accounts.models import User
            return User.objects(id=user_id).first()
            
        except Exception as e:
            logger.error(f"Error in secure_user_lookup: {e}")
            return None
    
    @staticmethod
    def secure_notice_access_check(notice_id, user):
        """Secure notice access check"""
        try:
            # Validate notice_id
            if not notice_id or not isinstance(notice_id, str):
                return False
            
            if not re.match(r'^[a-f0-9]{24}$', notice_id):
                logger.warning(f"Invalid notice_id format: {notice_id}")
                return False
            
            from .models import Notice
            notice = Notice.objects(id=notice_id).first()
            
            if not notice:
                return False
            
            # Check if user is owner
            if notice.owner and str(notice.owner.id) == str(user.id):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in secure_notice_access_check: {e}")
            return False
    
    @staticmethod
    def secure_response_filter(notice_id):
        """Secure response filtering for notices"""
        try:
            # Validate notice_id
            if not notice_id or not isinstance(notice_id, str):
                return None
            
            if not re.match(r'^[a-f0-9]{24}$', notice_id):
                logger.warning(f"Invalid notice_id for response filter: {notice_id}")
                return None
            
            from .models import Notice, Response
            notice = Notice.objects(id=notice_id).first()
            
            if not notice:
                return None
            
            return Response.objects(notice=notice)
            
        except Exception as e:
            logger.error(f"Error in secure_response_filter: {e}")
            return None

def sanitize_mongo_input(data):
    """Sanitize input for MongoDB operations"""
    if not data:
        return data
    
    if isinstance(data, str):
        # Remove dangerous MongoDB operators
        dangerous_patterns = [
            r'\$ne',
            r'\$gt',
            r'\$lt',
            r'\$gte',
            r'\$lte',
            r'\$in',
            r'\$nin',
            r'\$regex',
            r'\$where',
            r'\$exists',
            r'\$or',
            r'\$and',
            r'\$not',
            r'\$nor',
        ]
        
        sanitized = data
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    elif isinstance(data, dict):
        sanitized_dict = {}
        for key, value in data.items():
            # Only allow safe keys
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                sanitized_dict[key] = sanitize_mongo_input(value)
            else:
                logger.warning(f"Unsafe MongoDB key detected: {key}")
        
        return sanitized_dict
    
    elif isinstance(data, list):
        return [sanitize_mongo_input(item) for item in data]
    
    else:
        return data

class SecureMongoDBAggregation:
    """Secure MongoDB aggregation pipeline builder"""
    
    @staticmethod
    def build_notice_stats_pipeline():
        """Build secure aggregation pipeline for notice statistics"""
        # Use fixed, safe aggregation pipeline
        pipeline = [
            {
                '$group': {
                    '_id': '$type',
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'count': -1}
            }
        ]
        
        return pipeline
    
    @staticmethod
    def build_user_activity_pipeline(user_id):
        """Build secure aggregation pipeline for user activity"""
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            return []
        
        if not re.match(r'^[a-f0-9]{24}$', user_id):
            logger.warning(f"Invalid user_id in aggregation: {user_id}")
            return []
        
        # Use parameterized aggregation
        pipeline = [
            {
                '$match': {
                    'owner_id': user_id
                }
            },
            {
                '$group': {
                    '_id': '$status',
                    'count': {'$sum': 1}
                }
            }
        ]
        
        return pipeline
