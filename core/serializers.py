from rest_framework.serializers import ModelSerializer, Serializer, EmailField, CharField, IntegerField, SlugRelatedField
from core.models import User

class UserSerializer(ModelSerializer):
    password = CharField(write_only=True)
    country = SlugRelatedField(read_only=True, slug_field='name_text__pt_br')
    state = SlugRelatedField(read_only=True, slug_field='code')
    municipality = SlugRelatedField(read_only=True, slug_field='name')
    
    class Meta:
        model = User
        fields = (
            'email',
            'password',
            'first_name',
            'last_name',
            'occupation',
            'company',
            'country',
            'state',
            'municipality',
        )

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
