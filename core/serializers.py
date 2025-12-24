from django.db import transaction
from django.db.models import Prefetch, Q
from rest_framework.serializers import BooleanField, CharField, DateTimeField, EmailField, IntegerField, JSONField, ModelSerializer, Serializer, ValidationError
from core.models import Content, ContentEndorsement, Source, SourceField, SourceFieldValue, SourceType, User
from jsonschema import validate, FormatChecker
import json

class SourceFieldSerializer(ModelSerializer):
    name = CharField(read_only=True, source='name_text.pt_br')
    description = CharField(read_only=True, source='description_text.pt_br')
    schema = JSONField(read_only=True)

    class Meta:
        model = SourceField
        fields = (
            'id',
            'name',
            'description',
            'schema',
            'is_nullable',
            'position',
        )

class SourceFieldValueSerializer(ModelSerializer):
    # read
    field = CharField(read_only=True, source='field.name_text.pt_br')
    schema = JSONField(read_only=True, source='field.schema')
    position = IntegerField(read_only=True, source='field.position')
    # write
    value = CharField()
    field_id = IntegerField(write_only=True)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        
        if obj.field.schema['type'] != "string":
            data['value'] = json.loads(obj.value)

        return data

    def to_internal_value(self, data):
        value = data.get('value')
        field_id = data.get('field_id')

        try:
            field = SourceField.objects.denormalized().active().get(id=field_id)
        except SourceField.DoesNotExist:
            raise ValidationError({'field_id': f"Não há campo cadastrado com o id {field_id}."})

        if field.schema['type'] != "string":
            data['value'] = json.dumps(value)

        self.field = field
        self.loaded_value = value

        return super().to_internal_value(data) # default method must run after custom so that it validates 'value' as string

    def validate(self, data):
        field = self.field
        value = self.loaded_value

        try:
            validate(value, field.schema, format_checker=FormatChecker())
        except Exception as e:
            raise ValidationError({'value': f"Valor inválido para o campo '{field.name_text.pt_br}' (field_id: {field.id})': {e}"})
        
        return data

    class Meta:
        model = SourceFieldValue
        fields = (
            'field',
            'field_id',
            'value',
            'schema',
            'position',
        )

class SourceSerializer(ModelSerializer):
    # read
    id = IntegerField(read_only=True)
    type = CharField(read_only=True, source='type.name_text.pt_br')
    is_static = BooleanField(read_only=True, source='type.is_static')
    created_at = DateTimeField(read_only=True)
    deleted_at = DateTimeField(read_only=True)
    # both
    field_values = SourceFieldValueSerializer(many=True)
    creator_id = IntegerField()
    # write
    type_id = IntegerField(write_only=True)
    creator_notes = CharField(write_only=True, required=False, max_length=300, allow_null=True, allow_blank=True)

    def validate_required_fields(self, data, type_fields):
        required_fields = type_fields.filter(is_nullable=False)
        passed_field_ids = [item['field_id'] for item in data['field_values']]
        missing_req_field_errors = []
        for req in required_fields:
            if req.id not in passed_field_ids:
                missing_req_field_errors.append({
                    'field_values': f"Campo '{req.name_text.pt_br}' obrigatório (field_id: {req.id})."
                })

        if missing_req_field_errors:
            raise ValidationError(missing_req_field_errors)

    def validate_uniqueness(self, data, type, type_fields):
        type_sources = Source.objects.active().filter(
            Q(type_id=type.id) | Q(type__parent_id=type.id)
        ).select_related(
            'type',
        ).prefetch_related(
            Prefetch(
                'field_values',
                queryset=SourceFieldValue.objects.active().select_related(
                    'field',
                ).order_by(
                    'field__position',
                )
            ),
        ).order_by('-created_at')
        
        field_positions = {field.id: field.position for field in type_fields}
        data['field_values'].sort(key=lambda item: field_positions[item['field_id']])

        for source in type_sources:
            source_field_values = [{'field_id': item.field_id, 'value': item.value} for item in source.field_values.all()]
            if data['field_values'] == source_field_values and (type.is_static or source.creator_id == data['creator_id']):
                raise ValidationError({'non_field_errors': f"Já existe outra fonte cadastrada com os mesmos dados: [{source.id}]."})

    def validate(self, data):
        type = SourceType.objects.active().get(id=data['type_id'])
        fields = SourceField.objects.denormalized().active()

        type_fields = fields.filter(source_type_id=type.id)
        if type.parent_id:
            type_fields |= fields.filter(source_type_id=type.parent_id)

        self.validate_required_fields(data, type_fields)
        self.validate_uniqueness(data, type, type_fields)

        return data

    def create(self, validated_data):
        with transaction.atomic():
            source = Source.objects.create(
                type_id = validated_data['type_id'],
                creator_id = validated_data['creator_id'],
                creator_notes = validated_data.get('creator_notes'),
            )

            SourceFieldValue.objects.bulk_create([
                SourceFieldValue(
                    source_id = source.id,
                    field_id = item['field_id'],
                    value = item['value'],
                ) for item in validated_data['field_values']
            ])

            return source

    class Meta:
        model = Source
        fields = (
            'id',
            'type',
            'is_static',
            'field_values',
            'type_id',
            'creator_id',
            'creator_notes',
            'created_at',
            'deleted_at',
        )

class SourceTypeSerializer(ModelSerializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True, source='name_text.pt_br')
    is_static = BooleanField(read_only=True)
    level = CharField(read_only=True, source='get_level_display')
    parent_id = IntegerField(read_only=True)
    fields = SourceFieldSerializer(many=True, read_only=True, source='field_set')

    class Meta:
        model = SourceType
        fields = (
            'id',
            'name',
            'level',
            'parent_id',
            'is_static',
            'fields',
        )

class UserSerializer(ModelSerializer):
    country = CharField(read_only=True)
    state = CharField(read_only=True)
    municipality = CharField(read_only=True)
    
    class Meta():
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'occupation',
            'company',
            'country',
            'state',
            'municipality',
        ]

class UserPreviewSerializer(UserSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
        ]

class UserCreationSerializer(Serializer):
    email = EmailField(max_length=255)
    password = CharField(max_length=128)
    first_name = CharField(max_length=30)
    last_name = CharField(max_length=50)
    occupation = CharField(max_length=30)
    company = CharField(max_length=30, required=False, allow_blank=True)
    country = CharField(required=False, allow_null=True)
    state = CharField(required=False, allow_null=True)
    municipality = CharField(required=False, allow_null=True)

class UserUpdateSerializer(Serializer):
    email = CharField(max_length=255)
    first_name = CharField(max_length=30)
    last_name = CharField(max_length=50)
    occupation = CharField(max_length=30)
    company = CharField(max_length=30, required=False, allow_blank=True)
    country = CharField(required=False, allow_null=True)
    state = CharField(required=False, allow_null=True)
    municipality = CharField(required=False, allow_null=True)

class UserTokenCreationSerializer(Serializer):
    email = EmailField(max_length=255)
    password = CharField(max_length=128)

class ContentParamsSerializer(Serializer):
    with_user_endorsement_info = BooleanField(required=False)

class ContentSerializer(ModelSerializer):
    # both
    source_id = IntegerField(required=False, source='content.source_id')
    # write
    content_proposer_id = IntegerField(write_only=True)
    content_proposer_comment = CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    # read
    content_status = CharField(read_only=True, source='content.status')
    content_proposer = UserPreviewSerializer(read_only=True, source='content.proposer')
    endorsements_count = IntegerField(read_only=True, source='content.endorsements_count')
    proposed_at = DateTimeField(read_only=True, source='content.proposed_at')
    accepted_at = DateTimeField(read_only=True, source='content.accepted_at')
    rejected_at = DateTimeField(read_only=True, source='content.rejected_at')
    
    def __init__(self,  *args, **kwargs):
        self.content_type = kwargs.pop('content_type')

        self.params = kwargs.pop('content_params', {})
        if self.params.get('with_user_endorsement_info'):
            self.fields['is_endorsed_by_user'] = BooleanField(read_only=True)
            self.fields['user_endorsement_id'] = IntegerField(read_only=True)

        super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if self.params.get('with_user_endorsement_info'):
            user_endorsements = obj.content.endorsements.all() # user-specific endorsements (prefetched on queryset)
            data['is_endorsed_by_user'] = True if user_endorsements else False
            data['user_endorsement_id'] = user_endorsements[0].id if user_endorsements else None

        return data

    def to_internal_value(self, data):
        return data # must skip default method to avoid source_id nesting on write
    
    def validate(self, data):
        if self.content_type != 'plant' and not data.get('source_id'):
            raise ValidationError({'source_id': "Campo obrigatório."})
        
        return data

    def create(self, validated_data):
        return Content.objects.create(
            status = 'proposed',
            type = self.content_type,
            source_id = validated_data.get('source_id'),
            proposer_id = validated_data.get('content_proposer_id'),
            proposer_comment = validated_data.get('content_proposer_comment'),
        )

    class Meta:
        model = Content
        fields = [
            'source_id',
            'content_status',
            'content_proposer',
            'content_proposer_id',
            'content_proposer_comment',
            'endorsements_count',
            'proposed_at',
            'accepted_at',
            'rejected_at',
        ]

class ContentEndorsementParamsSerializer(Serializer):
    content_id = IntegerField(required=False)

class ContentEndorsementSerializer(ModelSerializer):
    # read
    id = IntegerField(read_only=True)
    endorser = UserPreviewSerializer(read_only=True)
    created_at = DateTimeField(read_only=True)
    # write
    endorser_id = IntegerField(write_only=True)
    # both
    content_id = IntegerField()

    def validate(self, data):
        try:
            content = Content.objects.get(id=data.get('content_id'))
        except Content.DoesNotExist:
            raise ValidationError({'content_id': "Não há conteúdo cadastrado com esse id."})
        
        if data.get('endorser_id') == content.proposer_id:
            raise ValidationError({'endorser_id': "Somente outro usuário pode apoiar conteúdo criado por você."})

        if ContentEndorsement.objects.active().filter(content_id=data.get('content_id'), endorser_id=data.get('endorser_id')):
            raise ValidationError({'non_field_errors': "Apoio já cadastrado."})

        return data
        
    def create(self, validated_data):
        with transaction.atomic():
            endorsement = ContentEndorsement.objects.create(**validated_data)

            endorsement.content.endorsements_count += 1
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
