import json

from django.http import HttpResponse, JsonResponse

from .models import CustomUser, Image


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


def get_images(request, user_id):
    """Get images."""
    if request.method == 'GET':
        try:
            images = Image.objects.filter(user_id=user_id)
            results = [{
                'id': image.pk,
                'user_id': image.user.pk,
                'url': image.url,
                'original_uri': image.original_uri,
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

        user, _ = CustomUser.objects.get_or_create(id=data.get('user_id'))
        image.user = user
        image.save()
        results = [{
            'id': image.pk,
            'user_id': image.user.pk,
            'url': image.url,
            'original_uri': image.original_uri,
            'tags': list(image.tags.order_by('-score').values_list('name', flat=True)),
        }]
        return JsonResponse({'results': results})


def get_image(request, user_id, image_id):
    """Get image."""
    try:
        images = Image.objects.filter(user_id=user_id, id=image_id)
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
