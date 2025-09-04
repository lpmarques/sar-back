from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import URLValidator
from rest_framework.serializers import ModelSerializer, Serializer, EmailField, CharField, IntegerField, SlugRelatedField, ValidationError
from core.models import Content, ContentEndorsement, Source, User
import re

class SourceSerializer(ModelSerializer):
    content_author_id = IntegerField(write_only=True, allow_null=False)

    def validate_url(self, value):
        try:
            URLValidator(value)
        except ValidationError as e:
            raise ValidationError('URL inválida.')
        
        return value
    
    def validate_publication_authors(self, value):
        for author in value:
            if re.match(r'/^(([A-Z][a-z]+ ?(d[eao][sl]? )?){2,})|((d[eao][sl]? )?[A-Z][a-z]+,? ([A-Z]\. ?)+)$/', author):
                raise ValidationError(f'Autor inválido: {author}. Formatos aceitos: "Nome Sobrenome" ou "Sobrenome N."')
        
        return value

    class Meta:
        model = Source
        fields = (
            'id',
            'type',
            'year',
            'title',
            'authors',
            'publisher',
            'url',
            'description',
            'content_author_id',
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

class ContentEndorsementSerializer(ModelSerializer):
    # read
    id = IntegerField(read_only=True)
    endorser = UserPreviewSerializer(read_only=True)
    created_at = CharField(read_only=True)
    # write
    endorser_id = IntegerField(write_only=True, required=True)
    # both
    content_id = IntegerField()

    def validate(self, data):
        try:
            content = Content.objects.get(id=data.get('content_id'))
        except Content.DoesNotExist:
            raise ValidationError("Não há conteúdo cadastrado com esse content_id.")
        
        if data.get('endorser_id') == content.proposer_id:
            raise ValidationError("Somente outro usuário pode aprovar conteúdo criado por você.")

        if ContentEndorsement.objects.active().filter(content_id=data.get('content_id'), endorser_id=data.get('endorser_id')):
            raise ValidationError("Aprovação já cadastrada.")

        return data
        
    def create(self, validated_data):
        endorsement = ContentEndorsement.objects.create(**validated_data)

        endorsement.content.endorsements += 1
        endorsement.content.save()

        return endorsement

    class Meta:
        model = ContentEndorsement
        fields = [
            'id',
            'endorser',
            'endorser_id',
            'content_id',
            'created_at',
        ]

class UserContentEndorsementSerializer(ContentEndorsementSerializer):    
    class Meta:
        model = ContentEndorsement
        fields = [
            'id',
            'content_id',
            'created_at',
        ]

class ContentEndorsementParamsSerializer(Serializer):
    content_id = IntegerField(required=False)