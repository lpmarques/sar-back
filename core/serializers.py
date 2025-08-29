from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import URLValidator
from rest_framework.serializers import ModelSerializer, Serializer, EmailField, CharField, IntegerField, SerializerMethodField, SlugRelatedField, ValidationError
from core.models import ContentEndorsement, Source, User
from catalog.models import PlantNaturalOccurrenceRegion, PlantPopularName, PlantScientificName, PlantValue
import re

class SourceSerializer(ModelSerializer):
    content_author_id = IntegerField(allow_null=False)

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
            'publication_title',
            'publication_authors',
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

class EndorsementValidationMixin:
    content_type_to_fk = {
        'plant_value': 'plant_value_id',
        'plant_popular_name': 'plant_popular_name_id',
        'plant_scientific_name': 'plant_scientific_name_id',
        'plant_natural_occurrence_region': 'plant_natural_occurrence_region_id',
    }

    def validate_content_type(self, value):
        if value not in self.content_type_to_fk.keys():
            raise ValidationError("Tipo de conteúdo inválido.")
        
        return value

    def validate(self, data):
        content_type = data.get('content_type')
        content_id_field = self.content_type_to_fk.get(content_type)
        content_id = data.get(content_id_field)
        if content_type and not content_id:
            raise ValidationError(f"Tipo '{content_type}' foi passado, mas campo '{content_id_field}' está ausente.")
        
        self.endorsement_key = {
            'endorser_id': data.get('endorser_id'),
            'content_type': content_type,
            content_id_field: content_id,
        }

        return data

class ContentEndorsementSerializer(EndorsementValidationMixin, ModelSerializer):
    # read
    id = IntegerField(read_only=True)
    endorser = UserPreviewSerializer(read_only=True)
    created_at = CharField(read_only=True)
    # write
    endorser_id = IntegerField(write_only=True, required=True)
    #both
    content_type = CharField(required=True)
    plant_value_id = IntegerField(required=False, allow_null=True)
    plant_popular_name_id = IntegerField(required=False, allow_null=True)
    plant_scientific_name_id = IntegerField(required=False, allow_null=True)
    plant_natural_occurrence_region_id = IntegerField(required=False, allow_null=True)

    def validate_content_type(self, value):
        return super().validate_content_type(value)

    def validate(self, data):
        return super().validate(data)
        
    def create(self, validated_data):
        content_type = validated_data['content_type']
        content_id_field = self.content_type_to_fk.get(content_type)
        content_id = validated_data.get(content_id_field)

        if ContentEndorsement.objects.filter(**self.endorsement_key, deleted_at=None):
            raise ValidationError("Confirmação já cadastrada.")
        
        try:
            if content_type == 'plant_value':
                content = PlantValue.objects.get(id=content_id)
            elif content_type == 'plant_popular_name':
                content = PlantPopularName.objects.get(id=content_id)
            elif content_type == 'plant_scientific_name':
                content = PlantScientificName.objects.get(id=content_id)
            elif content_type == 'plant_natural_occurrence_region':
                content = PlantNaturalOccurrenceRegion.objects.get(id=content_id)
        except ObjectDoesNotExist:
            raise ValidationError("Conteúdo inexistente.")
        
        if validated_data.get('endorser_id') == content.content_author:
            raise ValidationError("Somente outro usuário pode aprovar conteúdo criado por você.")

        content.endorsements += 1
        content.save()

        return ContentEndorsement.objects.create(**validated_data)

    class Meta:
        model = ContentEndorsement
        fields = [
            'id',
            'endorser',
            'endorser_id',
            'content_type',
            'plant_value_id',
            'plant_popular_name_id',
            'plant_scientific_name_id',
            'plant_natural_occurrence_region_id',
            # 'plant_invasion_risk_region_id',
            'created_at',
        ]

class UserContentEndorsementSerializer(ModelSerializer, EndorsementValidationMixin):
    def validate_content_type(self, value):
        return super().validate_content_type(value)

    def validate(self, data):
        return super().validate(data)
    
    class Meta:
        model = ContentEndorsement
        fields = [
            'id',
            'content_type',
            'plant_value_id',
            'plant_popular_name_id',
            'plant_scientific_name_id',
            'plant_natural_occurrence_region_id',
            # 'plant_invasion_risk_region_id',
            'created_at',
        ]

class ContentEndorsementParamsSerializer(Serializer, EndorsementValidationMixin):
    def validate_content_type(self, value):
        return super().validate_content_type(value)

    def validate(self, data):
        return super().validate(data)
    
    content_type = CharField(required=False)
    plant_value_id = CharField(required=False)
    plant_popular_name_id = CharField(required=False)
    plant_scientific_name_id = CharField(required=False)
