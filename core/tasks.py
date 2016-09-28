import base64
import json
import logging
import os
from io import BytesIO

import requests
from celery import task

from .models import Image, Result, Tag


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
def analyze(url=None, image_pk=None, save=False):
    """Analyze."""
    logging.info('Analyze image')
    if url is None and image_pk is None:
        return True

    if url is None:
        image = Image.objects.get(id=image_pk)
        url = image.url

    microsoft_cognitive.delay(url=url, image_pk=image_pk, save=save)

    response = requests.get(url)
    image_byte = BytesIO(response.content).read()
    image_content = base64.b64encode(image_byte).decode('utf-8')

    # Async
    google_vision.delay(url=url, image_pk=image_pk, image_content=image_content, save=save)

    # Sync
    craftar_search(url=url, image_pk=image_pk, image_byte=image_byte, save=save)
    return True


@task
def craftar_search(url=None, image_pk=None, image_byte=None, save=False):
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
    data = response.json()

    if 'results' in data:
        image = Image.objects.get(id=image_pk)
        for craftar_data in data['results']:
            result = Result(
                image=image,
                name=craftar_data.get('name'),
                category=Result.AI,
                service=Result.CRAFTAR,
            )
            if os.getenv('DATABASE_URL', '').startswith('postgres'):
                result.payload = json.dumps(craftar_data)
            result.save()

    return data


@task
def google_vision(url=None, image_pk=None, image_content=None, save=False):
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

    if 'responses' in result and image_pk and save:
        image = Image.objects.get(id=image_pk)
        image.tags.filter(category=Tag.AI, service=Tag.GOOGLE).delete()
        for feature, feature_data in result['responses'][0].items():
            if feature == 'labelAnnotations':
                for tag_data in feature_data:
                    logging.debug('Google vision Tag: {}'.format(tag_data.get('description')))
                    tag = Tag(
                        image=image,
                        name=tag_data.get('description'),
                        score=tag_data.get('score'),
                        category=Tag.AI,
                        service=Tag.GOOGLE,
                        locale='en',
                        is_valid=True,
                    )
                    if os.getenv('DATABASE_URL', '').startswith('postgres'):
                        tag.payload = json.dumps(tag_data)
                    tag.save()

            elif feature == 'logoAnnotations':
                Result.objects.filter(
                    image=image,
                    category=Result.AI,
                    service=Result.GOOGLE,
                    feature=Result.LOGO,
                ).delete()
                for logo_data in feature_data:
                    logging.debug('Google vision Logo: {}'.format(logo_data.get('description')))
                    result = Result.objects.create(
                        image=image,
                        name=logo_data.get('description'),
                        category=Result.AI,
                        service=Result.GOOGLE,
                        feature=Result.LOGO,
                    )
                    if os.getenv('DATABASE_URL', '').startswith('postgres'):
                        result.payload = json.dumps(logo_data)
                    result.save()

            elif feature == 'textAnnotations':
                Result.objects.filter(
                    image=image,
                    category=Result.AI,
                    service=Result.GOOGLE,
                    feature=Result.TEXT,
                ).delete()
                for text_data in feature_data:
                    logging.debug('Google vision Text: {}'.format(text_data.get('description')))
                    result = Result.objects.create(
                        image=image,
                        name=text_data.get('description'),
                        category=Result.AI,
                        service=Result.GOOGLE,
                        feature=Result.TEXT,
                    )
                    if os.getenv('DATABASE_URL', '').startswith('postgres'):
                        result.payload = json.dumps(text_data)
                    result.save()

    return request.json()


@task
def microsoft_cognitive(url=None, image_pk=None, save=False):
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
        'https://api.projectoxford.ai/vision/v1.0/analyze?visualFeatures=Categories,Tags,Description,Faces,Adult&details=Celebrities',  # noqa
        headers=headers,
        json=payload
    )

    response = request.json()

    if image_pk and save:
        if 'tags' in response:
            image = Image.objects.get(id=image_pk)
            image.tags.filter(category=Tag.AI, service=Tag.MICROSOFT).delete()
            for tag_data in response['tags']:
                logging.debug('Tag: {}'.format(tag_data.get('name')))
                tag = Tag(
                    image=image,
                    name=tag_data.get('name'),
                    score=tag_data.get('confidence'),
                    category=Tag.AI,
                    service=Tag.MICROSOFT,
                    locale='en',
                    is_valid=True,
                )
                if os.getenv('DATABASE_URL', '').startswith('postgres'):
                    tag.payload = json.dumps(tag_data)
                tag.save()

        if 'adult' in response:
            result, _ = Result.objects.get_or_create(
                image=image,
                category=Result.AI,
                service=Result.MICROSOFT,
                feature=Result.ADULT,
            )
            if os.getenv('DATABASE_URL', '').startswith('postgres'):
                result.payload = json.dumps(response['adult'])
            result.save()

        if 'categories' in response:
            for category in response['categories']:
                if 'detail' in category and 'celebrities' in category['detail']:
                    Result.objects.filter(
                        image=image,
                        category=Result.AI,
                        service=Result.MICROSOFT,
                        feature=Result.CELEBRITY,
                    ).delete()
                    for celebrity in category['detail']['celebrities']:
                        result = Result.objects.create(
                            image=image,
                            name=celebrity.get('name'),
                            category=Result.AI,
                            service=Result.MICROSOFT,
                            feature=Result.CELEBRITY,
                        )
                        if os.getenv('DATABASE_URL', '').startswith('postgres'):
                            result.payload = json.dumps(celebrity)
                        result.save()

        if 'description' in response and 'captions' in response['description']:
            Result.objects.filter(
                image=image,
                category=Result.AI,
                service=Result.MICROSOFT,
                feature=Result.DESCRIPTION,
            ).delete()
            for caption in response['description']['captions']:
                result = Result.objects.create(
                    image=image,
                    name=caption.get('text'),
                    category=Result.AI,
                    service=Result.MICROSOFT,
                    feature=Result.DESCRIPTION,
                )
                if os.getenv('DATABASE_URL', '').startswith('postgres'):
                    result.payload = json.dumps(caption)
                result.save()

        if 'faces' in response:
            Result.objects.filter(
                image=image,
                category=Result.AI,
                service=Result.MICROSOFT,
                feature=Result.FACE,
            ).delete()
            for face in response['faces']:
                result = Result.objects.create(
                    image=image,
                    category=Result.AI,
                    service=Result.MICROSOFT,
                    feature=Result.FACE,
                )
                if os.getenv('DATABASE_URL', '').startswith('postgres'):
                    result.payload = json.dumps(face)
                result.save()

    return response


# @task
# def sync_firebase():
#     """Sync firebase."""
#     return True
