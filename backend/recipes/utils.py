import base64

from django.core.files.base import ContentFile


def decode_image(image_data, name):
    if isinstance(image_data, str) and image_data.startswith('data:image'):
        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1]
        return ContentFile(base64.b64decode(imgstr), name=f'{name}.{ext}')
    return None
