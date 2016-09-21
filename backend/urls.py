from django.conf.urls import include, url
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^core/', include('core.urls')),

    url(r'^graphql', csrf_exempt(GraphQLView.as_view(graphiql=True))),
]
