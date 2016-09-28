from django.contrib import admin
from django_object_actions import DjangoObjectActions

from .models import CustomUser, Image, Result, Tag


class ImageAdmin(DjangoObjectActions, admin.ModelAdmin):

    """ImageAdmin."""

    def analyze_this(self, request, obj):
        obj.analyze(True)

    def make_analyzed(modeladmin, request, queryset):
        for obj in queryset.all():
            obj.analyze(True)

    list_display = ('url', 'image_tag')
    change_actions = ('analyze_this', )
    changelist_actions = ('make_analyzed', )


# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Image, ImageAdmin)
admin.site.register(Tag)
admin.site.register(Result)
