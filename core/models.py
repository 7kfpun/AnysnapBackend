import json
import os
import uuid
from itertools import groupby

import pyrebase
import requests
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.core.cache import cache
from django.db import models
from django.utils.html import format_html

config = {
    'apiKey': 'KKNRgC46ZvryQKlseI4DpONiUhmNPDh2YDwfSPzO',
    'authDomain': 'frontn-anysnap.firebaseapp.com',
    'databaseURL': 'https://frontn-anysnap.firebaseio.com',
    'storageBucket': 'frontn-anysnap-images',
}

firebase = pyrebase.initialize_app(config)


class CustomUser(AbstractUser):

    """CustomUser."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    notification_player_id = models.CharField(max_length=36, blank=True, null=True)

    @property
    def pk_str(self):
        """String pk."""
        return str(self.pk)


class ImageManager(models.Manager):

    """Image Manager."""

    def create_analytics(self, url, original_uri, user=None):
        """Create analytics."""
        image = self.create(url=url, original_uri=original_uri)
        image.user = user
        image.save()
        image.analyze()
        return image


class Image(models.Model):

    """Image model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        blank=True, null=True,
        related_name='images',
    )
    url = models.CharField(max_length=255)
    original_uri = models.CharField(max_length=1024, blank=True, null=True)

    is_recommended = models.BooleanField(default=False)
    is_master = models.BooleanField(default=False)

    is_public = models.BooleanField(default=False)

    is_analyzed = models.BooleanField(default=False)
    is_synced = models.BooleanField(default=False)

    is_banned = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)

    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    objects = ImageManager()

    @property
    def pk_str(self):
        """String pk."""
        return str(self.pk)

    def analyze(self, save=False):
        """Analyze."""
        from .tasks import analyze
        task = analyze.delay(image_pk=self.pk_str, save=save)
        cache.set('image-analyze-{}'.format(self.pk_str), task.id, 5 * 60)
        return task

    def get_analytic_task(self):
        """Get task."""
        from .tasks import analyze
        task_pk = cache.get('image-analyze-{}'.format(self.pk_str))
        return analyze.AsyncResult(task_pk)

    def notice(self):
        """Notice user."""
        return True

    def sync_firebase(self):
        """Sync firebase."""
        db = firebase.database()
        db.child('results').child(self.pk_str).set(self.get_results())
        return True

    def send_notification(self):
        """Send notification."""
        if self.user:
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Authorization': 'Basic NDNhNzkwZDUtODI4Yi00NDcyLWE1NjctY2NkM2EwMmUwMGM5',
            }
            payload = {
                'app_id': 'dc288eac-7909-4101-81ec-53720528d547',
                'contents': {'en': 'New message received'},
                'include_player_ids': [self.user.notification_player_id],
            }
            payload['data'] = {
                'id': self.pk_str,
            }

            request = requests.post(
                'https://onesignal.com/api/v1/notifications',
                headers=headers,
                json=payload,
            )
            request_json = request.json()
            if 'id' in request_json:
                self.is_sent = True
                self.save()
            return request_json
        return False

    def get_results(self):
        """Get results."""
        results = [{
            'name': result.name,
            'category': result.get_category_display(),
            'service': result.get_service_display(),
            'feature': result.get_feature_display(),
            'payload': json.loads(result.payload) if result.payload else result.payload,
        } for result in self.results.filter(is_valid=True)]

        def keyfn(x):
            return x['feature'].lower()
        data = dict((k, list(g)) for k, g in groupby(sorted(results, key=keyfn), keyfn))

        if os.getenv('DATABASE_URL', '').startswith('postgres'):
            data['tag'] = [{
                'name': tag.name,
                'score': tag.score,
            } for tag in self.tags.filter(is_valid=True).order_by('-score').distinct('name')]
        else:
            data['tag'] = [{
                'name': tag.name,
                'score': tag.score,
            } for tag in self.tags.filter(is_valid=True).order_by('-score')]
        return data

    def image_tag(self):
        """Image tag."""
        return format_html('<img src="{}" height="100" />', self.url)

    def results_tag(self):
        """Results_tag."""
        return json.dumps(self.get_results())[:600]

    def __str__(self):
        """__str__."""
        return self.url


class Tag(models.Model):

    """Tag model."""

    AI = 'AI'
    HUMAN = 'HU'
    CATEGORY_CHOICES = (
        (AI, 'AI'),
        (HUMAN, 'Human'),
    )

    GOOGLE = 'GO'
    MICROSOFT = 'MI'
    SERVICE_CHOICES = (
        (GOOGLE, 'Google Vision'),
        (MICROSOFT, 'Microsoft Cognitive'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name='tags',
        related_query_name='tag',
        blank=True, null=True
    )
    name = models.CharField(max_length=255)
    score = models.FloatField(blank=True, null=True)
    category = models.CharField(
        max_length=2,
        choices=CATEGORY_CHOICES,
        default=AI,
        blank=True, null=True
    )
    service = models.CharField(
        max_length=2,
        choices=SERVICE_CHOICES,
        default=GOOGLE,
        blank=True, null=True
    )
    user = models.ForeignKey(
        CustomUser,
        blank=True, null=True,
        related_name='tags',
    )
    locale = models.CharField(max_length=10, default='en')
    is_valid = models.BooleanField(default=True)
    payload = JSONField(blank=True, null=True)

    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    def image_tag(self):
        """Image tag."""
        return format_html('<img src="{}" height="80" />', self.image.url)

    def __str__(self):
        """__str__."""
        return str(self.name)


class Result(models.Model):

    """Result model."""

    AI = 'AI'
    HUMAN = 'HU'
    CATEGORY_CHOICES = (
        (AI, 'AI'),
        (HUMAN, 'Human'),
    )

    GOOGLE = 'GO'
    MICROSOFT = 'MI'
    CRAFTAR = 'CR'
    SERVICE_CHOICES = (
        (GOOGLE, 'Google Vision'),
        (MICROSOFT, 'Microsoft Cognitive'),
        (CRAFTAR, 'Craftar'),
    )

    # Microsoft
    CATEGORY = 'CA'
    CELEBRITY = 'CE'
    DESCRIPTION = 'DE'
    ADULT = 'AD'
    TEXT = 'TE'
    FACE = 'FA'

    # Google
    LOGO = 'LO'

    # Craftar
    RECOGNITION = 'RE'

    # Others
    MAP = 'MA'
    PHONE = 'PH'
    URL = 'UR'
    FEATURE_CHOICES = (
        (CATEGORY, 'Category'),
        (CELEBRITY, 'Celebrity'),
        (DESCRIPTION, 'Description'),
        (ADULT, 'Adult'),
        (TEXT, 'Text'),
        (FACE, 'Face'),

        (LOGO, 'Logo'),

        (RECOGNITION, 'Recognition'),

        (MAP, 'Map'),
        (PHONE, 'Phone'),
        (URL, 'Url'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name='results',
        related_query_name='result',
        blank=True, null=True
    )
    name = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(
        max_length=2,
        choices=CATEGORY_CHOICES,
        default=AI,
        blank=True, null=True
    )
    service = models.CharField(
        max_length=2,
        choices=SERVICE_CHOICES,
        blank=True, null=True
    )
    feature = models.CharField(
        max_length=2,
        choices=FEATURE_CHOICES,
        blank=True, null=True
    )
    user = models.ForeignKey(
        CustomUser,
        blank=True, null=True,
        related_name='results',
    )
    locale = models.CharField(max_length=10, default='en')
    is_valid = models.BooleanField(default=True)
    payload = JSONField(blank=True, null=True)

    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    def image_tag(self):
        """Image tag."""
        return format_html('<img src="{}" height="80" />', self.image.url)

    def __str__(self):
        """__str__."""
        return str(self.name)


class Notification(models.Model):

    """Notification model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        related_name='notifications',
    )
    image = models.ForeignKey(
        Image,
        related_name='notifications',
        related_query_name='notification',
    )
    payload = JSONField(blank=True, null=True)
    is_sent = models.BooleanField(default=False)

    def send(self):
        """Send."""
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': 'Basic NDNhNzkwZDUtODI4Yi00NDcyLWE1NjctY2NkM2EwMmUwMGM5',
        }
        payload = {
            'app_id': 'dc288eac-7909-4101-81ec-53720528d547',
            'contents': {'en': 'New message received'},
            'include_player_ids': [self.user.notification_player_id],
        }
        if self.image:
            payload['data'] = {
                'id': self.image.pk_str,
            }

        request = requests.post(
            'https://onesignal.com/api/v1/notifications',
            headers=headers,
            json=payload,
        )
        request_json = request.json()
        if 'id' in request_json:
            self.is_sent = True
            self.save()
        return request_json
