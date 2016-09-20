from django.contrib import admin

from .models import CustomUser, Image, Tag, Result

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Image)
admin.site.register(Tag)
admin.site.register(Result)
