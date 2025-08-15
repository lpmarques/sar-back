from rest_framework.serializers import CharField, IntegerField, ModelSerializer, SerializerMethodField, SlugRelatedField
from catalog.models import Plant, PlantNaturalOccurrenceRegion, PlantPopularName, PlantScientificName, PlantTrait, PlantValue
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

class TraitSerializer(ModelSerializer):
    key = CharField(read_only=True, source='name')
    name = SlugRelatedField(read_only=True, source='name_text', slug_field='pt_br')
    section_key = CharField(read_only=True, source='section')
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
            'key',
            'name',
            'section_key',
            'section_name',
            'type',
            'is_nullable',
            'numeric_value_min',
            'numeric_value_max',
            'text_value_options',
        ]

class PlantTraitValuePreviewSerializer(ModelSerializer):
    trait_key = SlugRelatedField(read_only=True, source='trait', slug_field='name')
    trait_name = SlugRelatedField(read_only=True, source='trait', slug_field='name_text__pt_br')
    type = SerializerMethodField()
    value = SerializerMethodField()

    def get_type(self, obj):
        return pg_to_json_type.get(obj.trait.data_type)

    def get_value(self, obj):
        value = obj.value
        data_type = obj.trait.data_type

        if data_type == 'int4range' or data_type == 'numrange':
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

    class Meta:
        model = PlantValue
        fields = [
            'id',
            'trait_key',
            'trait_name',
            'type',
            'value',
        ]

class PlantTraitValueSerializer(PlantTraitValuePreviewSerializer):
    section_key = SlugRelatedField(read_only=True, source='trait', slug_field='section')
    section_name = SlugRelatedField(read_only=True, source='trait', slug_field='section_text__pt_br')
    boundaries = SerializerMethodField()
    content_author = UserPreviewSerializer()
    source = SourceSerializer()

    def get_boundaries(self, obj):
        data_type = obj.trait.data_type

        if data_type == 'int4range' or data_type == 'numrange':
            return {
                "minimum": obj.trait.numeric_value_min,
                "maximum": obj.trait.numeric_value_max
            }
        if data_type == "varchar" or data_type == "varchar[]":
            return [item.option_text.pt_br for item in obj.trait.text_value_options.all()]
        if data_type == "boolean":
            return [True, False]

    class Meta(PlantTraitValuePreviewSerializer.Meta):
        model = PlantValue
        fields = PlantTraitValuePreviewSerializer.Meta.fields + [
            'section_key',
            'section_name',
            'boundaries',
            'content_status',
            'content_author',
            'source',
            'endorsements',
            'created_at',
            'accepted_at',
            'rejected_at',
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

class PlantNaturalOccurrenceRegionPreviewSerializer(ModelSerializer):
    country = SlugRelatedField(read_only=True, slug_field='name_text__pt_br')
    state = SlugRelatedField(read_only=True, slug_field='code')
    biome = SlugRelatedField(read_only=True, slug_field='name')
    vegetation_type = SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = PlantNaturalOccurrenceRegion
        fields = [
            'country',
            'state',
            'biome',
            'vegetation_type',
        ]

class PlantNaturalOccurrenceRegionSerializer(PlantNaturalOccurrenceRegionPreviewSerializer):
    content_author = UserPreviewSerializer(read_only=True)
    source = SourceSerializer(read_only=True)

    class Meta(PlantNaturalOccurrenceRegionPreviewSerializer.Meta):
        fields = PlantNaturalOccurrenceRegionPreviewSerializer.Meta.fields + [
            'content_status',
            'content_author',
            'source',
            'created_at',
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
