import uuid

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

    def image_tag(self):
        """Image tag."""
        return format_html('<img src="{}" height="100" />', self.url)


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
        return format_html('<img src="{}" height="100" />', self.image.url)

    def __str__(self):
        """__str__."""
        return self.name


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
    DESCRIBE = 'DE'
    ADULT = 'AD'
    TEXT = 'TE'
    FACE = 'FA'

    LOGO = 'LO'

    MAP = 'MA'
    PHONE = 'PH'
    URL = 'UR'
    FEATURE_CHOICES = (
        (CATEGORY, 'Category'),
        (DESCRIBE, 'Describe'),
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
        default=URL,
        blank=True, null=True
    )
    feature = models.CharField(
        max_length=2,
        choices=FEATURE_CHOICES,
        default=CATEGORY,
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

    def __str__(self):
        """__str__."""
        return self.name
