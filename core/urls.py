from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^users/(?P<user_id>[\w-]+)/images/$', views.get_images),
    url(r'^users/(?P<user_id>[\w-]+)/images/(?P<image_id>[\w-]+)$', views.get_image),

    url(r'^public_images/$', views.get_public_images),
]
