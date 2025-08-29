from rest_framework.serializers import CharField, DateTimeField, IntegerField, ListField, ModelSerializer, Serializer, SerializerMethodField, SlugRelatedField, ValidationError
from catalog.models import Plant, PlantNaturalOccurrenceRegion, PlantPopularName, PlantScientificName, PlantTrait, PlantValue, PlantValueText
from core.models import Text
from core.serializers import SourceSerializer, UserPreviewSerializer
import json

pg_to_json_type = {
    'int4range': 'range',
    'numrange': 'range',
    'varchar[]': 'string[]',
    'varchar': 'string',
    'integer': 'number',
    'boolean': 'boolean'
}

class WritableSerializerMethodField(SerializerMethodField):
    def __init__(self, **kwargs):
        self.setter_method_name = kwargs.pop('setter_method_name', None)

        super().__init__(**kwargs)

        self.read_only = False

    def bind(self, field_name, parent):
        retval = super().bind(field_name, parent)
        if not self.setter_method_name:
            self.setter_method_name = f'set_{field_name}'

        return retval

    def get_default(self):
        default = super().get_default()

        return {
            self.field_name: default
        }

    def to_internal_value(self, value):
        method = getattr(self.parent, self.setter_method_name)
        return {self.field_name: method(value)}

class TraitSerializer(ModelSerializer):
    id = IntegerField(read_only=True)
    slug = CharField(read_only=True, source='name')
    name = SlugRelatedField(read_only=True, source='name_text', slug_field='pt_br')
    section_slug = CharField(read_only=True, source='section')
    section_name = SlugRelatedField(read_only=True, source='section_text', slug_field='pt_br')
    type = SerializerMethodField()
    is_nullable = CharField(read_only=True)
    numeric_value_min = IntegerField(read_only=True)
    numeric_value_max = IntegerField(read_only=True)
    text_value_options = SlugRelatedField(read_only=True, many=True, slug_field='option_text__pt_br')

    def get_type(self, obj):
        return pg_to_json_type.get(obj.data_type)

    class Meta:
        model = PlantTrait
        fields = [
            'id',
            'slug',
            'name',
            'section_slug',
            'section_name',
            'type',
            'is_nullable',
            'numeric_value_min',
            'numeric_value_max',
            'text_value_options',
        ]

class TraitValueSerializer(ModelSerializer):
    # read
    id = IntegerField(read_only=True)
    trait_slug = SlugRelatedField(read_only=True, source='trait', slug_field='name')
    trait_name = SlugRelatedField(read_only=True, source='trait', slug_field='name_text__pt_br')
    section_slug = SlugRelatedField(read_only=True, source='trait', slug_field='section')
    section_name = SlugRelatedField(read_only=True, source='trait', slug_field='section_text__pt_br')
    type = SerializerMethodField()
    boundaries = SerializerMethodField()
    content_status = CharField(read_only=True)
    content_author = UserPreviewSerializer(read_only=True)
    source = SourceSerializer(read_only=True)
    endorsements = IntegerField(read_only=True)
    created_at = DateTimeField(read_only=True)
    accepted_at = DateTimeField(read_only=True)
    rejected_at = DateTimeField(read_only=True)
    # write
    source_id = IntegerField(write_only=True, required=True)
    content_author_id = IntegerField(write_only=True, required=True)
    content_author_comment = CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    # both
    value = WritableSerializerMethodField(setter_method_name='set_value_field')
    trait_id = IntegerField(required=True)
    plant_id = IntegerField(required=True)

    def get_type(self, obj):
        return pg_to_json_type.get(obj.trait.data_type)

    def get_value(self, obj):
        value = obj.value
        data_type = obj.trait.data_type

        if data_type in ['int4range', 'numrange']:
            min, max = json.loads(value)
            return {
                "minimum": min,
                "maximum": max
            }
        elif data_type == "varchar[]":
            return [item.text.pt_br for item in obj.plant_value_texts.all()]
        elif data_type == "varchar":
            items = obj.plant_value_texts.all()
            return items[0].text.pt_br if len(items) > 0 else value # TODO: todos os valores textuais deveriam existir na plant_value_texts (nomes das famílias precisam constar na texts ou então deixar de ser um trait)
        else:
            return json.loads(value)

    def get_boundaries(self, obj):
        data_type = obj.trait.data_type

        if data_type in ['int4range', 'numrange']:
            return {
                "minimum": obj.trait.numeric_value_min,
                "maximum": obj.trait.numeric_value_max
            }
        if data_type == "varchar" or data_type == "varchar[]":
            return [item.option_text.pt_br for item in obj.trait.text_value_options.all()]
        if data_type == "boolean":
            return [True, False]
        
    def set_value_field(self, value): # called before validation
        return value
    
    def value_to_string_value(self, value): # called before writing
        if self.trait.data_type in ['int4range', 'numrange']:
            return json.dumps([value.get('minimum'), value.get('maximum')])
        elif self.trait.data_type in ["varchar", "varchar[]"]:
            values = value if self.trait.data_type == "varchar[]" else [value]
            texts = Text.objects.filter(**{'pt_br__in': values})
            return json.dumps(sorted([text.en for text in texts]))

        return json.dumps(value)

    def validate(self, data):
        value = data.get('value')

        try:
            self.trait = PlantTrait.objects.denormalized().get(id=data.get('trait_id'))
        except PlantTrait.DoesNotExist:
            raise ValidationError("Traço inexistente.")

        matching_values = PlantValue.objects.filter(
            plant_id=data['plant_id'],
            trait_id=self.trait.id,
            content_status__in=["accepted", "proposed"],
            value=self.value_to_string_value(value),
        )
        if matching_values:
            raise ValidationError("Valor igual ao valor aceito ou a outra proposta já cadastrada.")

        if self.trait.data_type in ["varchar", "varchar[]"]:
            values = value if self.trait.data_type == "varchar[]" else [value]
            if len(values) == 0:
                raise ValidationError("Valor não pode ser vazio.")
            options = TraitSerializer(self.trait).data.get('text_value_options')
            for item in values:
                if item not in options:
                    raise ValidationError(
                        f"Valor '{item}' inválido para o traço. Valores permitidos: {json.dumps(options)}"
                    )
        if self.trait.data_type == "number":
            if value >= self.trait.numeric_value_min and value <= self.trait.numeric_value_max:
                raise ValidationError(
                    f"Valor '{value}' fora do intervalo permitido para o traço: de {self.trait.numeric_value_min} até {self.trait.numeric_value_max}"
                )
        if self.trait.data_type == "range":
            if (value.get('minimum') >= value.get('maximum')):
                raise ValidationError("O valor mínimo do intervalo não pode ser inferior ao valor máximo")
            if (value.get('minimum') < self.trait.numericValueMin):
                raise ValidationError(f"O valor mínimo está fora do intervalo permitido para o traço: de {self.trait.numeric_value_min} até {self.trait.numeric_value_max}")
            if (value.get('maximum') > self.trait.numericValueMax):
                raise ValidationError(f"O valor máximo está fora do intervalo permitido para o traço: de {self.trait.numeric_value_min} até {self.trait.numeric_value_max}")
            
        return data
        
    def create(self, validated_data):
        value = validated_data.get('value')

        validated_data['content_status'] = 'proposed'
        validated_data['value'] = self.value_to_string_value(value)
        validated_data['trait_id'] = self.trait.id
        validated_data.pop('trait_slug', None)

        trait_value = PlantValue.objects.create(**validated_data)

        if self.trait.data_type in ["varchar", "varchar[]"]:
            list = value if self.trait.data_type == "varchar[]" else [value]
            texts = Text.objects.filter(**{'pt_br__in': list})
            value_texts = [PlantValueText(plant_value_id=trait_value.id, text_id=text.id) for text in texts]
            PlantValueText.objects.bulk_create(value_texts)

        return trait_value

    class Meta:
        model = PlantValue
        fields = [
            'id',
            'trait_id',
            'plant_id',
            'trait_slug',
            'trait_name',
            'section_slug',
            'section_name',
            'type',
            'value',
            'boundaries',
            'source',
            'source_id',
            'content_status',
            'content_author',
            'content_author_id',
            'content_author_comment',
            'endorsements',
            'created_at',
            'accepted_at',
            'rejected_at',
        ]

class PlantTraitValueSerializer(TraitValueSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data.pop('plant_id', None)

        return data

class PlantTraitValuePreviewSerializer(PlantTraitValueSerializer):
    class Meta:
        model = PlantValue
        fields = [
            'id',
            'trait_slug',
            'trait_name',
            'type',
            'value',
        ]

class ScientificNameSerializer(ModelSerializer):
    class Meta:
        model = PlantScientificName
        fields = [
            'name',
            'taxonomic_status',
            'content_status',
            'plant_id',
        ]

class PlantScientificNameSerializer(ScientificNameSerializer):
    content_author = UserPreviewSerializer()
    source = SourceSerializer()

    class Meta:
        model = PlantScientificName
        fields = [
            'name',
            'taxonomic_status',
            'content_status',
            'content_author',
            'endorsements',
            'source',
            'created_at',
            'accepted_at',
        ]

class PopularNameSerializer(ModelSerializer):
    class Meta:
        model = PlantPopularName
        fields = [
            'name',
            'content_status',
            'plant_id',
        ]

class PlantPopularNameSerializer(PopularNameSerializer):
    content_author = UserPreviewSerializer()
    source = SourceSerializer()
    
    class Meta:
        model = PlantPopularName
        fields = [
            'name',
            'content_status',
            'content_author',
            'endorsements',
            'source',
            'created_at',
            'accepted_at',
        ]

class NaturalOccurrenceRegionSerializer(Serializer):
    country = CharField(read_only=True, source='country__name_text__pt_br')
    state = CharField(read_only=True, source='state__code')
    biome = CharField(read_only=True, source='biome__name')
    vegetation_type = CharField(read_only=True, source='vegetation_type__name')
    plant_ids = ListField(read_only=True)

class PlantNaturalOccurrenceRegionSerializer(ModelSerializer):
    country = SlugRelatedField(read_only=True, slug_field='name_text__pt_br')
    state = SlugRelatedField(read_only=True, slug_field='code')
    biome = SlugRelatedField(read_only=True, slug_field='name')
    vegetation_type = SlugRelatedField(read_only=True, slug_field='name')
    content_author = UserPreviewSerializer(read_only=True)
    source = SourceSerializer(read_only=True)

    class Meta:
        model = PlantNaturalOccurrenceRegion
        fields = [
            'country',
            'state',
            'biome',
            'vegetation_type',
            'content_status',
            'content_author',
            'source',
            'created_at',
        ]

class PlantNaturalOccurrenceRegionPreviewSerializer(PlantNaturalOccurrenceRegionSerializer):
    class Meta:
        model = PlantNaturalOccurrenceRegion
        fields = [
            'country',
            'state',
            'biome',
            'vegetation_type',
        ]

class PlantSerializer(ModelSerializer):
    def __init__(self,  *args, **kwargs):
        params = kwargs.pop('params', {})
        if params.get('with_scientific_names'):
            self.fields['scientific_names'] = SlugRelatedField(many=True, read_only=True, slug_field='name')
        if params.get('with_popular_names'):
            self.fields['popular_names'] = SlugRelatedField(many=True, read_only=True, slug_field='name')
        if params.get('with_trait_values'):
            self.fields['trait_values'] = PlantTraitValuePreviewSerializer(many=True, read_only=True, source='values')
        if params.get('with_natural_occurrence_regions'):
            self.fields['natural_occurrence_regions'] = PlantNaturalOccurrenceRegionPreviewSerializer(many=True, read_only=True)

        super().__init__(*args, **kwargs)

    class Meta:
        model = Plant
        fields = [
            'id',
            'content_status',
            'accepted_scientific_name',
            'created_at',
            'accepted_at',
        ]
