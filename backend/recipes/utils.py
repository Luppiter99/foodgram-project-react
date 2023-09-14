import base64
import re

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile


def validate_color(value):
    pattern = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
    if not re.match(pattern, value):
        raise ValidationError(f'{value} is not a valid HEX color')


def decode_image(image_data, name):
    if isinstance(image_data, str) and image_data.startswith('data:image'):
        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1]
        return ContentFile(base64.b64decode(imgstr), name=f'{name}.{ext}')
    return None
