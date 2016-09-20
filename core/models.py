import uuid

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):

    """CustomUser."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)


class Image(models.Model):

    """Image model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        blank=True, null=True,
        related_name="images",
    )
    url = models.CharField(max_length=255)

    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        """__str___."""
        return self.url


class Tag(models.Model):

    """Tag model."""

    AI = 'AI'
    ADMIN = 'AA'
    USER = 'UU'
    CATEGORY_CHOICES = (
        (AI, 'AI'),
        (ADMIN, 'Admin'),
        (USER, 'User'),
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
    category = models.CharField(
        max_length=2,
        choices=CATEGORY_CHOICES,
        default=AI,
        blank=True, null=True
    )
    user = models.CharField(max_length=255, blank=True, null=True)
    locale = models.CharField(max_length=10, default='en')
    isValid = models.BooleanField(default=True)

    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        """__str___."""
        return self.name


class Result(models.Model):

    """Result model."""

    MAP = 'MA'
    PHONE = 'PH'
    URL = 'UR'
    CATEGORY_CHOICES = (
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
    name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=2,
        choices=CATEGORY_CHOICES,
        default=URL,
        blank=True, null=True
    )
    user = models.CharField(max_length=255, blank=True, null=True)
    locale = models.CharField(max_length=10, default='en')
    isValid = models.BooleanField(default=True)
    payload = JSONField(blank=True, null=True)

    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        """__str___."""
        return self.name
