from rest_framework import serializers
from .models import User, Profile


class ProfileSerializer(serializers.Serializer):
    bio = serializers.CharField(required=False, allow_blank=True, max_length=500)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    location = serializers.CharField(required=False, allow_blank=True, max_length=100)
    website = serializers.CharField(required=False, allow_blank=True, max_length=200)
    github_username = serializers.CharField(required=False, allow_blank=True, max_length=100)
    linkedin_username = serializers.CharField(required=False, allow_blank=True, max_length=100)
    twitter_username = serializers.CharField(required=False, allow_blank=True, max_length=100)
    skills = serializers.ListField(child=serializers.CharField(max_length=50), required=False)
    experience_years = serializers.IntegerField(required=False, min_value=0)
    education = serializers.CharField(required=False, allow_blank=True, max_length=200)
    company = serializers.CharField(required=False, allow_blank=True, max_length=100)
    job_title = serializers.CharField(required=False, allow_blank=True, max_length=100)

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        
        # Calculate completion percentage and update status
        instance.calculate_completion_percentage()
        instance.save()
        return instance


class UserSerializer(serializers.Serializer):
    user_id = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    nickname = serializers.CharField(read_only=True)
    profile_image = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    profile = ProfileSerializer(read_only=True)

    def to_representation(self, instance):
        # Get or create profile for the user
        try:
            profile = Profile.objects(user=instance).first()
        except:
            profile = None

        data = {
            'id': instance.user_id,  # Use user_id as the frontend id
            'user_id': instance.user_id,
            'username': instance.username,
            'email': instance.email,
            'nickname': instance.nickname,
            'profile_image': self.get_image_url(instance),
            'created_at': instance.created_at,
            'profile': ProfileSerializer(profile).data if profile else None
        }
        return data
    
    def get_image_url(self, instance):
        if instance.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/auth/profile/image/{instance.user_id}/')
            return f'/auth/profile/image/{instance.user_id}/'
        return None


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    nickname = serializers.CharField(max_length=100, required=False, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    profile_image = serializers.ImageField(write_only=True, required=False)

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        
        # Check if email already exists
        if User.objects(email=attrs['email'].lower()).first():
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})
        
        # Check if username already exists
        if User.objects(username=attrs['username']).first():
            raise serializers.ValidationError({'username': 'A user with this username already exists.'})
        
        return attrs

    def create(self, validated_data):
        profile_image = validated_data.pop('profile_image', None)
        user = User.create_user(**validated_data)
        if profile_image:
            user.profile_image = profile_image
            user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class ProfileUpdateSerializer(serializers.Serializer):
    """Serializer for updating user profile information"""
    nickname = serializers.CharField(required=False, allow_blank=True, max_length=100)
    profile_image = serializers.ImageField(required=False)
    bio = serializers.CharField(required=False, allow_blank=True, max_length=500)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    location = serializers.CharField(required=False, allow_blank=True, max_length=100)
    website = serializers.CharField(required=False, allow_blank=True, max_length=200)
    github_username = serializers.CharField(required=False, allow_blank=True, max_length=100)
    linkedin_username = serializers.CharField(required=False, allow_blank=True, max_length=100)
    twitter_username = serializers.CharField(required=False, allow_blank=True, max_length=100)
    skills = serializers.ListField(child=serializers.CharField(max_length=50), required=False)
    experience_years = serializers.IntegerField(required=False, min_value=0)
    education = serializers.CharField(required=False, allow_blank=True, max_length=200)
    company = serializers.CharField(required=False, allow_blank=True, max_length=100)
    job_title = serializers.CharField(required=False, allow_blank=True, max_length=100)

    def update(self, instance, validated_data):
        # Update user fields
        user_fields = ['nickname', 'profile_image']
        for field in user_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        # Update profile fields
        profile_fields = [
            'bio', 'phone', 'location', 'website', 'github_username',
            'linkedin_username', 'twitter_username', 'skills',
            'experience_years', 'education', 'company', 'job_title'
        ]
        
        try:
            profile = Profile.objects(user=instance).first()
            if not profile:
                profile = Profile.objects.create(user=instance)
            
            for field in profile_fields:
                if field in validated_data:
                    setattr(profile, field, validated_data[field])
            
            profile.calculate_completion_percentage()
            profile.save()
        except Exception as e:
            # If profile update fails, continue with user update
            pass
        
        instance.save()
        return instance
