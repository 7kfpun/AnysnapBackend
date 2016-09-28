import json

from django.contrib import admin
from django.utils.safestring import mark_safe
from django_object_actions import DjangoObjectActions
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer

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

    def data_prettified(self, instance):
        """Prettify data."""
        response = json.dumps(instance.get_results(), sort_keys=True, indent=2)
        response = response[:5000]

        formatter = HtmlFormatter(style='colorful')
        response = highlight(response, JsonLexer(), formatter)

        style = "<style>" + formatter.get_style_defs() + "</style><br>"

        return mark_safe(style + response)

    list_display = ('url', 'image_tag', 'results_tag')
    change_actions = ('analyze_this', )
    actions = ('make_analyzed', )

    readonly_fields = ('image_tag', 'data_prettified')

    data_prettified.short_description = 'data prettified'


class TagAdmin(DjangoObjectActions, admin.ModelAdmin):

    """TagAdmin."""

    list_display = ('name', 'image_tag', 'score', 'is_valid')


class ResultAdmin(DjangoObjectActions, admin.ModelAdmin):

    """ResultAdmin."""

    list_display = ('name', 'image_tag', 'category', 'service', 'feature', 'is_valid')


# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Image, ImageAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Result, ResultAdmin)
