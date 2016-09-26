import base64
import logging
from io import BytesIO

import requests
from celery import task

from .models import Image, Tag


@task(bind=True)
def debug_task(self):
    """debug_task."""
    print('Request: {0!r}'.format(self.request))


@task
def add(x, y):
    """Add."""
    logging.info('Adding {0} + {1}'.format(x, y))
    return x + y


@task
def analyze(url=None, image_pk=None):
    """Analyze."""
    logging.info('Analyze image')
    if url is None and image_pk is None:
        return True

    if url is None:
        image = Image.objects.get(id=image_pk)
        url = image.url

    microsoft_cognitive.delay(image_pk=image.pk)

    response = requests.get(url)
    image_byte = BytesIO(response.content).read()
    image_content = base64.b64encode(image_byte).decode('utf-8')

    # Async
    google_vision.delay(url=url, image_content=image_content)

    # Sync
    # craftar_search(url, image_byte)
    return True


@task
def craftar_search(url=None, image_pk=None, image_byte=None):
    """Update."""
    logging.info('CraftAR search')
    if url is None and image_pk is None and image_byte is None:
        return True

    if url is None:
        image = Image.objects.get(id=image_pk)
        url = image.url

    if not image_byte:
        response = requests.get(url)
        image_byte = BytesIO(response.content).read()

    craftar_token = '519618cc98234d89'
    payload = {
        'token': (None, craftar_token),
        'image': ('image.jpg', image_byte),
    }
    response = requests.post(
        'https://search.craftar.net/v1/search',
        files=payload,
    )
    result = response.json()

    if 'results' in result and result['results']:
        pass

    return result


@task
def google_vision(url=None, image_pk=None, image_content=None):
    """Google vision."""
    logging.info('Google vision')
    if url is None and image_pk is None and image_content is None:
        return True

    if url is None:
        image = Image.objects.get(id=image_pk)
        url = image.url

    if not image_content:
        response = requests.get(url)
        image_byte = BytesIO(response.content).read()
        image_content = base64.b64encode(image_byte).decode('utf-8')

    gcloud_vision = 'AIzaSyDDAh-r_u4ZqPrhvPV8cBVha-EOb3vqbHg'
    payload = {
        'requests': [
            {
                'image': {
                    'content': image_content,
                },
                'features': [
                    {
                        'type': 'LABEL_DETECTION',
                        'maxResults': 10,
                    },
                    {
                        'type': 'LOGO_DETECTION',
                        'maxResults': 5,
                    },
                    {
                        'type': 'TEXT_DETECTION',
                        'maxResults': 15,
                    },
                ],
            },
        ],
    }
    request = requests.post(
        'https://vision.googleapis.com/v1/images:annotate?key={}'.format(gcloud_vision),
        json=payload
    )

    result = request.json()

    if 'tags' in result:
        for tag_data in result['tags']:
            tag = Tag(
                image_id=image_pk,
                name=tag_data.get('name'),
                category=Tag.AI,
                service=Tag.MICROSOFT,
                locale='en',
                payload=tag_data,
            )
            tag.save()
    return request.json()


@task
def microsoft_cognitive(url=None, image_pk=None):
    """Microsoft cognitive."""
    logging.info('Microsoft cognitive')
    if url is None and image_pk is None:
        return True

    if url is None:
        image = Image.objects.get(id=image_pk)
        url = image.url

    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': '5f9521ea68574897b1bafc0c015f7382',
    }
    payload = {
        'url': url
    }
    request = requests.post(
        'https://api.projectoxford.ai/vision/v1.0/analyze?visualFeatures=Categories,Tags,Description,Faces,Adult',
        headers=headers,
        json=payload
    )

    result = request.json()

    if 'responses' in result:
        for response_data in result['responses']:
            if 'labelAnnotations' in response_data:
                for tag_data in response_data['labelAnnotations']:
                    tag = Tag(
                        image_id=image_pk,
                        name=tag_data.get('description'),
                        category=Tag.AI,
                        service=Tag.GOOGLE,
                        locale='en',
                        payload=tag_data,
                    )
                    tag.save()

            elif 'logoAnnotations' in response_data:
                pass

            elif 'textAnnotations' in response_data:
                pass

    return result


# @task
# def sync_firebase():
#     """Sync firebase."""
#     return True
