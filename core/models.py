import uuid
import json

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.core.cache import cache
from django.db import models
from django.utils.html import format_html


class CustomUser(AbstractUser):

    """CustomUser."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)


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
        related_name="images",
    )
    url = models.CharField(max_length=255)
    original_uri = models.CharField(max_length=1024, blank=True, null=True)

    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    objects = ImageManager()

    def __str__(self):
        """__str__."""
        return self.url

    @property
    def pk_str(self):
        """String pk."""
        return str(self.pk)

    def analyze(self, save=False):
        """Analyze."""
        from .tasks import analyze
        task = analyze.delay(image_pk=self.pk_str, save=save)
        cache.set('image-analyze-{}'.format(self.pk_str), task.id, 5 * 60)

    def get_task(self):
        """Get task."""
        from .tasks import analyze
        task_pk = cache.get('image-analyze-{}'.format(self.pk_str))
        return analyze.AsyncResult(task_pk)

    def get_results(self):
        """Get results."""
        return {
            "tags": [{
                "name": tag.name,
                "score": tag.score,
            } for tag in self.tags.filter(is_valid=True)],
            "results": [{
                "name": result.name,
                "category": result.category,
                "service": result.service,
                "feature": result.feature,
            } for result in self.results.filter(is_valid=True)]
        }

    def image_tag(self):
        """Image tag."""
        return format_html('<img src="{}" height="100" />', self.url)

    def results_tag(self):
        """Results_tag."""
        return json.dumps(self.get_results())


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
        related_name="tags",
        related_query_name="tag",
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
        related_name="tags",
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

    LOGO = 'LO'

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

        (MAP, 'Map'),
        (PHONE, 'Phone'),
        (URL, 'Url'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name="results",
        related_query_name="result",
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
        related_name="results",
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
