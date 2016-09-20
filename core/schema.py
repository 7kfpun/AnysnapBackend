import graphene

from graphene_django import DjangoObjectType
from graphene import Field, relay

from graphene_django.filter import DjangoFilterConnectionField

from .models import CustomUser, Image, Tag, Result


def connection_for_type(_type):
    """connection_for_type."""
    class Connection(graphene.Connection):
        total_count = graphene.Int()

        class Meta:
            name = _type._meta.name + 'Connection'
            node = _type

        def resolve_total_count(self, args, context, info):
            return self.length

    return Connection


class UserNode(DjangoObjectType):

    """UserNode."""

    class Meta:
        model = CustomUser
        exclude_fields = (
            'date_joined',
            'first_name',
            'is_active',
            'is_staff',
            'is_superuser',
            'last_login',
            'last_name',
            'password',
            'username',
        )
        filter_fields = ('id', )
        interfaces = (relay.Node, )

UserNode.Connection = connection_for_type(UserNode)


class ImageNode(DjangoObjectType):

    """ImageNode."""

    class Meta:
        model = Image
        interfaces = (relay.Node, )


class TagNode(DjangoObjectType):

    """Tag."""

    class Meta:
        model = Tag
        interfaces = (relay.Node, )
        filter_fields = ['id', 'name']


class ResultNode(DjangoObjectType):

    """ResultNode."""

    class Meta:
        model = Result
        interfaces = (relay.Node, )


class Query(graphene.ObjectType):

    """Query."""

    hello = graphene.String(description='A typical hello world')

    user = Field(UserNode)
    all_users = DjangoFilterConnectionField(UserNode)

    image = Field(ImageNode)
    all_images = DjangoFilterConnectionField(ImageNode)

    tag = Field(TagNode)
    all_tags = DjangoFilterConnectionField(TagNode)

    result = Field(ResultNode)
    all_results = DjangoFilterConnectionField(ResultNode)

    def resolve_hello(self, args, context, info):
        """resolve_hello."""
        return 'World'


class CreateImage(relay.ClientIDMutation):

    """CreateImage."""

    class Input:
        url = graphene.String(required=True)
        user_id = graphene.String(required=True)
        user_email = graphene.String()

    image = graphene.Field(ImageNode)
    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        """mutate_and_get_payload."""
        url = input.get('url')
        user_id = input.get('user_id')
        user_email = input.get('user_email')
        user, _ = CustomUser.objects.get_or_create(id=user_id)
        if user_email:
            user.email = user_email
            user.save()
        image = Image.objects.create(url=url, user=user)
        return CreateImage(image=image, ok=bool(image.id))


class Mutation(graphene.ObjectType):

    """Mutation."""

    create_image = CreateImage.Field()


schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
)
