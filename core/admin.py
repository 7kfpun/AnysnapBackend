from django.contrib import admin
from django_object_actions import DjangoObjectActions

from .models import CustomUser, Image, Result, Tag


class ImageAdmin(DjangoObjectActions, admin.ModelAdmin):

    """ImageAdmin."""

    def analyze_this(self, request, obj):
        """Analyze this."""
        obj.analyze(True)

    def make_analyzed(modeladmin, request, queryset):
        """Make analyzed."""
        for obj in queryset:
            obj.analyze(True)

    list_display = ('url', 'image_tag', 'results_tag')
    change_actions = ('analyze_this', )
    actions = ('make_analyzed', )


class TagAdmin(DjangoObjectActions, admin.ModelAdmin):

    """TagAdmin."""

    list_display = ('name', 'image_tag', 'score', 'is_valid')


# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Image, ImageAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Result)
