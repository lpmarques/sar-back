from rest_framework.serializers import ModelSerializer, Serializer, EmailField, CharField, IntegerField, SlugRelatedField
from core.models import Source, User

class SourceSerializer(ModelSerializer):
    class Meta:
        model = Source
        fields = (
            'id',
            'type',
            'year',
            'publication_title',
            'publication_authors',
            'publisher',
            'url',
            'description',
        )

class UserPreviewSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
        ]

class UserSerializer(UserPreviewSerializer):
    country = SlugRelatedField(read_only=True, slug_field='name_text__pt_br')
    state = SlugRelatedField(read_only=True, slug_field='code')
    municipality = SlugRelatedField(read_only=True, slug_field='name')
    
    class Meta(UserPreviewSerializer.Meta):
        model = User
        fields = UserPreviewSerializer.Meta.fields + [
            'occupation',
            'company',
            'country',
            'state',
            'municipality',
        ]

class UserCreationSerializer(Serializer):
    email = EmailField(max_length=255)
    password = CharField(max_length=128)
    first_name = CharField(max_length=30)
    last_name = CharField(max_length=50)
    occupation = CharField(max_length=30)
    company = CharField(max_length=30, required=False, allow_blank=True)
    country_id = IntegerField(required=False, allow_null=True)
    state_id = IntegerField(required=False, allow_null=True)
    municipality_id = IntegerField(required=False, allow_null=True)

class UserUpdateSerializer(Serializer):
    email = CharField(max_length=255)
    first_name = CharField(max_length=30)
    last_name = CharField(max_length=50)
    occupation = CharField(max_length=30)
    company = CharField(max_length=30, required=False, allow_blank=True)
    country_id = IntegerField(required=False, allow_null=True)
    state_id = IntegerField(required=False, allow_null=True)
    municipality_id = IntegerField(required=False, allow_null=True)

class UserTokenCreationSerializer(Serializer):
    email = EmailField(max_length=255)
    password = CharField(max_length=128)
