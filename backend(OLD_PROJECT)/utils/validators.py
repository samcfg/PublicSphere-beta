# File: backend/utils/validators.py
import re
import requests
from django.core.validators import RegexValidator, URLValidator
from django.core.exceptions import ValidationError
from rest_framework.serializers import ValidationError as DRFValidationError
from urllib.parse import urlparse
import magic



# Username validator
username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Username can only contain letters, numbers, and @/./+/-/_ characters.'
)


# DOI validator
doi_regex = re.compile(r'^10\.\d{4,9}/[-.;()/:A-Z0-9]+$', re.IGNORECASE)
def validate_doi(value):
    """
    Validate if a string is a valid DOI
    """
    if not value:
        return
        
    if not doi_regex.match(value):
        raise ValidationError('Invalid DOI format. DOI should start with 10. followed by numbers.')


# URL validator with additional checks
def validate_url(url):
    """
    Extended URL validator that checks if the URL exists and is reachable
    """
    # Basic URL validation
    url_validator = URLValidator()
    try:
        url_validator(url)
    except ValidationError:
        raise ValidationError('Invalid URL format')
    
    # Parse the URL to check its components
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValidationError('URL must include scheme (http/https) and domain')
    
    # Optional: Check if URL is reachable
    # This can be turned off in production if it causes performance issues
    # try:
    #     response = requests.head(url, timeout=5)
    #     if response.status_code >= 400:
    #         raise ValidationError(f'URL returned error status: {response.status_code}')
    # except requests.RequestException:
    #     raise ValidationError('URL is not reachable')


# File type validator
def validate_file_type(file, allowed_types=None):
    """
    Validate file type using python-magic
    """
    if not allowed_types:
        allowed_types = ['pdf', 'docx', 'jpg', 'jpeg', 'png']
        
    # Get file mime type
    mime = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)  # Reset file pointer
    
    # Map mime types to extensions
    mime_to_ext = {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'image/jpeg': 'jpg',
        'image/png': 'png'
    }
    
    ext = mime_to_ext.get(mime)
    if not ext or ext not in allowed_types:
        raise ValidationError(f'Unsupported file type. Allowed types: {", ".join(allowed_types)}')


# File size validator
def validate_file_size(file, max_size_mb=5):
    """
    Validate that file size is within the allowed limit
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    if file.size > max_size_bytes:
        raise ValidationError(f'File size exceeds the limit of {max_size_mb}MB')


# Rating value validator
def validate_rating_value(value):
    """
    Validate that a rating value is between 0 and 100
    """
    if value < 0 or value > 100:
        raise ValidationError('Rating value must be between 0 and 100')


# Password strength validator
def validate_password_strength(password):
    """
    Validate password strength with custom requirements
    """
    if len(password) < 10:
        raise ValidationError('Password must be at least 10 characters long')
    
    if not any(char.isdigit() for char in password):
        raise ValidationError('Password must contain at least one digit')
    
    if not any(char.isalpha() for char in password):
        raise ValidationError('Password must contain at least one letter')
    
    if not any(not char.isalnum() for char in password):
        raise ValidationError('Password must contain at least one special character')


# Thread title validator
def validate_thread_title(title):
    """
    Validate thread title length and content
    """
    if len(title) < 5:
        raise ValidationError('Thread title must be at least 5 characters long')
    
    if len(title) > 255:
        raise ValidationError('Thread title must be less than 255 characters long')


# Comment content validator
def validate_comment_content(content):
    """
    Validate comment content length
    """
    if len(content) < 1:
        raise ValidationError('Comment cannot be empty')
    
    if len(content) > 10000:
        raise ValidationError('Comment must be less than 10,000 characters long')