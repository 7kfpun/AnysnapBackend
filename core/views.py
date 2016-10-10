import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import CustomUser, Image, Notification, Result


def index(request):
    """index."""
    return HttpResponse("Hello, world. You're at the polls index.")


def create_image(request):
    """Create image."""
    return None


def get_recommended_images(request):
    """Get recommended images."""
    images = Image.objects.filter(is_recommended=True)
    results = [{
        'id': image.pk,
        'url': image.url,
    } for image in images]
    return JsonResponse({'results': results})


def get_public_images(request):
    """Get public images."""
    images = Image.objects.filter(is_public=True, is_banned=False)
    results = [{
        'id': image.pk,
        'user_id': image.user.pk,
        'url': image.url,
    } for image in images]
    return JsonResponse({'results': results})


@csrf_exempt
def get_images(request, user_id):
    """Get images."""
    if request.method == 'GET':
        try:
            images = Image.objects.filter(user_id=user_id, is_deleted=False).order_by('-created_datetime')[:100]
            results = [{
                'id': image.pk,
                'user_id': image.user.pk,
                'url': image.url,
                'original_uri': image.original_uri,
                'created_datetime': image.created_datetime,
                'modified_datetime': image.modified_datetime,
            } for image in images]
            return JsonResponse({'results': results})
        except ValueError:
            return JsonResponse({'results': []})

    elif request.method == 'POST':
        data = json.loads(request.body.decode("utf-8"))
        image = Image.objects.create_analytics(
            url=data.get('url'),
            original_uri=data.get('original_uri'),
        )

        user, _ = CustomUser.objects.get_or_create(id=user_id, username=user_id)
        image.user = user
        image.save()
        image.analyze(save=True)
        image.sync_firebase()
        results = [{
            'id': image.pk,
            'user_id': image.user.pk,
            'url': image.url,
            'original_uri': image.original_uri,
        }]
        return JsonResponse({'results': results})


@csrf_exempt
def get_image(request, user_id, image_id):
    """Get image."""
    if request.method == 'GET':
        try:
            images = Image.objects.filter(user_id=user_id, id=image_id, is_deleted=False)
            results = [{
                'id': image.pk,
                'user_id': image.user.pk,
                'url': image.url,
                'original_uri': image.original_uri,
                'tags': list(image.tags.order_by('-score').values_list('name', flat=True)),
            } for image in images]
            return JsonResponse({'results': results})
        except ValueError:
            return JsonResponse({'results': []})
    elif request.method == 'DELETE':
        try:
            image = Image.objects.get(user_id=user_id, id=image_id, is_deleted=False)
            image.is_deleted = True
            image.save()
            return JsonResponse({'results': 'success'})
        except ValueError:
            return JsonResponse({'results': 'failure'})


@csrf_exempt
def get_notifications(request, user_id):
    """Get notifications."""
    if request.method == 'GET':
        try:
            notifications = Notification.objects \
                .filter(user_id=user_id, is_deleted=False) \
                .order_by('-created_datetime')[:100]
            results = [{
            } for notification in notifications]
            return JsonResponse({'results': results})
        except ValueError:
            return JsonResponse({'results': {}})


@csrf_exempt
def results_endpoint(request, user_id, image_id):
    """Get results."""
    if request.method == 'GET':
        try:
            image = Image.objects.get(user_id=user_id, is_deleted=False, id=image_id)
            return JsonResponse({'results': image.get_results()})
        except ValueError:
            return JsonResponse({'results': {}})

    elif request.method == 'POST':
        try:
            image = Image.objects.get(user_id=user_id, is_deleted=False, id=image_id)

            data = json.loads(request.body.decode("utf-8"))
            if data.get('payload'):
                Result.objects.create(
                    image_id=image_id,
                    category=Result.HUMAN,
                    name=data.get('payload', {}).get('type'),
                    feature=Result.CODE,
                    user_id=user_id,
                    payload=data.get('payload'),
                )
                image.sync_firebase()

            return JsonResponse({'results': image.get_results()})
        except ValueError:
            return JsonResponse({'results': {}})

        results = [{
            'id': image.pk,
            'user_id': image.user.pk,
            'url': image.url,
            'original_uri': image.original_uri,
        }]
        return JsonResponse({'results': results})
