import json

from django.contrib import admin
from django.utils.safestring import mark_safe
from django_object_actions import DjangoObjectActions
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer

from .models import CustomUser, Image, Notification, Result, Tag
from .tasks import sync_firebase


class UserAdmin(admin.ModelAdmin):

    """UserAdmin."""

    list_display = ('username', 'notification_player_id')
    list_filter = ('is_superuser', 'is_staff')


class ResultInline(admin.TabularInline):

    """ResultInline."""

    model = Result
    exclude = ['service', 'payload']

    def get_queryset(self, request):
        """get_queryset."""
        qs = super(ResultInline, self).get_queryset(request)
        return qs.filter(category=Result.HUMAN)


class ImageAdmin(DjangoObjectActions, admin.ModelAdmin):

    """ImageAdmin."""

    def analyze_this(self, request, obj):
        """Analyze this."""
        obj.analyze(save=True)

    def make_analyzed(modeladmin, request, queryset):
        """Make analyzed."""
        for obj in queryset:
            obj.analyze(save=True)

    def sync_this(self, request, obj):
        """Sync Firebase this."""
        # obj.sync_firebase()
        sync_firebase.delay(image_pk=obj.pk_str)

    def make_synced(modeladmin, request, queryset):
        """Make synced."""
        for obj in queryset:
            # obj.sync_firebase()
            sync_firebase.delay(image_pk=obj.pk_str)

    def send_notification_this(self, request, obj):
        """Send notification this."""
        if obj.send_notification():
            obj.is_sent = True
            obj.save()

    def make_sent_notification(modeladmin, request, queryset):
        """Make sent notification."""
        for obj in queryset:
            if obj.send_notification():
                obj.is_sent = True
                obj.save()

    def data_prettified(self, instance):
        """Prettify data."""
        response = json.dumps(instance.get_results(), sort_keys=True, indent=2)
        response = response[:30000]

        formatter = HtmlFormatter(style='colorful')
        response = highlight(response, JsonLexer(), formatter)

        button = '<button type="button" onclick="django.jQuery(\'.highlight\').toggle()">Click Me!</button>'
        script = '<script>django.jQuery(\'.highlight\').toggle()</script>'
        style = '<style>' + formatter.get_style_defs() + '</style><br>'

        return mark_safe(style + button + response + script)

    inlines = [ResultInline]

    list_display = ('image_small_tag', 'user', 'created_datetime',
                    'is_banned', 'is_analyzed', 'is_synced', 'is_sent_notification',
                    'is_deleted',
                    'results_tag')
    list_filter = ('is_recommended', 'is_master', 'is_public',
                   'is_banned', 'is_analyzed', 'is_synced', 'is_sent_notification')
    ordering = ('-created_datetime',)

    change_actions = ('analyze_this', 'sync_this', 'send_notification_this')
    actions = ('make_analyzed', 'make_synced', 'make_sent_notification')
    changelist_actions = ('make_synced', )

    readonly_fields = ('image_large_tag', 'data_prettified')

    data_prettified.short_description = 'data prettified'


class TagAdmin(DjangoObjectActions, admin.ModelAdmin):

    """TagAdmin."""

    list_display = ('name', 'image_tag', 'score', 'is_valid')
    list_filter = ('category', 'service', 'is_valid', 'locale')


class ResultAdmin(DjangoObjectActions, admin.ModelAdmin):

    """ResultAdmin."""

    list_display = ('name', 'image_tag', 'category', 'service', 'feature', 'is_valid')
    list_filter = ('category', 'service', 'feature', 'is_valid')


class NotificationAdmin(DjangoObjectActions, admin.ModelAdmin):

    """NotificationAdmin."""

    pass


# Register your models here.
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(Notification, NotificationAdmin)
