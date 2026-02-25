from mongoengine import Document, StringField, EmailField, DateTimeField, ImageField, IntField, ListField, ReferenceField
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import uuid


class User(Document):
    email = EmailField(required=True, unique=True)
    username = StringField(required=True, unique=True)
    nickname = StringField(max_length=100, default='')
    password = StringField(required=True)
    profile_image = ImageField()
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField(default=timezone.now)
    is_active = StringField(default='active')
    user_id = StringField(required=True, unique=True)  # Unique identifier
    auth_token = StringField(default='')  # Store auth token

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def set_password(self, raw_password):
        """Set password using Django's password hashing"""
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        """Check password using Django's password checking"""
        return check_password(raw_password, self.password)

    @classmethod
    def create_user(cls, email, username, password=None, **extra_fields):
        """Create a new user"""
        if not email:
            raise ValueError('Email is required')
        if not username:
            raise ValueError('Username is required')

        user = cls(
            email=email.lower(),
            username=username,
            user_id=str(uuid.uuid4()),
            **extra_fields
        )
        if password:
            user.set_password(password)
        user.save()
        
        # Create a profile for the user
        Profile.objects.create(user=user)
        
        return user

    class Meta:
        collection = 'users'


class Profile(Document):
    """Extended user profile information"""
    user = ReferenceField(User, required=True, unique=True)
    bio = StringField(max_length=500, default='')
    phone = StringField(max_length=20, default='')
    location = StringField(max_length=100, default='')
    website = StringField(max_length=200, default='')
    github_username = StringField(max_length=100, default='')
    linkedin_username = StringField(max_length=100, default='')
    twitter_username = StringField(max_length=100, default='')
    skills = ListField(StringField(max_length=50), default=[])
    experience_years = IntField(default=0)
    education = StringField(max_length=200, default='')
    company = StringField(max_length=100, default='')
    job_title = StringField(max_length=100, default='')
    profile_complete = StringField(default='incomplete')  # incomplete, partial, complete
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def calculate_completion_percentage(self):
        """Calculate profile completion percentage"""
        fields = [
            self.bio, self.phone, self.location, self.website,
            self.github_username, self.linkedin_username, self.twitter_username,
            self.education, self.company, self.job_title
        ]
        
        filled_fields = sum(1 for field in fields if field and field.strip())
        total_fields = len(fields)
        
        # Add skills and experience to the calculation
        if self.skills:
            filled_fields += 1
        total_fields += 1
        
        if self.experience_years > 0:
            filled_fields += 1
        total_fields += 1
        
        percentage = (filled_fields / total_fields) * 100
        
        # Update profile_complete status
        if percentage >= 90:
            self.profile_complete = 'complete'
        elif percentage >= 50:
            self.profile_complete = 'partial'
        else:
            self.profile_complete = 'incomplete'
        
        return percentage

    class Meta:
        collection = 'profiles'
