from rest_framework.serializers import Serializer, Field, BooleanField, CharField, DecimalField, IntegerField, ListField, ModelSerializer, SerializerMethodField, SlugRelatedField
from catalog.models import Plant, PlantPopularName, PlantScientificName, PlantTrait, PlantValue
import json

class StringListField(Field):
    def __init__(self, separator=",", *args, **kwargs):
        self.separator = separator
        super().__init__(*args, **kwargs)

    def to_internal_value(self, value):
        return self.separator.join(value) if value else None
    
    def to_representation(self, value):
        return value.split(self.separator) if value else None

class ScientificNameFilterParamsSerializer(Serializer):
    content_status = CharField(required=False, allow_blank=False, source='status')
    taxonomic_status = CharField(required=False, allow_blank=False)

class PopularNameFilterParamsSerializer(Serializer):
    content_status = CharField(required=False, allow_blank=False, source='status')

class TraitFilterParamsSerializer(Serializer):
    name__in = StringListField(required=False, allow_null=False, source='keys')
    section__in = StringListField(required=False, allow_null=False, source='section_keys')

class PlantTraitValueFilterParamsSerializer(Serializer):
    content_status = CharField(required=False, allow_blank=False, source='status')
    trait__name__in = StringListField(required=False, allow_null=False, source='trait_keys')
    trait__section__in = StringListField(required=False, allow_null=False, source='section_keys')

class PlantParamsSerializer(Serializer):
    status = BooleanField(required=False, allow_null=False)
    with_scientific_names = BooleanField(required=False, allow_null=False)
    scientific_names_status = CharField(required=False, allow_blank=False)
    scientific_names_taxonomic_status = CharField(required=False, allow_blank=False)
    with_popular_names = BooleanField(required=False, allow_null=False)
    popular_names_status = CharField(required=False, allow_blank=False)
    with_trait_values = BooleanField(required=False, allow_null=False)
    trait_values_status = CharField(required=False, allow_blank=False)
    trait_values_trait_keys = StringListField(required=False, allow_null=False)
    trait_values_section_keys = StringListField(required=False, allow_null=False)


class TraitSerializer(ModelSerializer):
    key = CharField(read_only=True, source='name')
    name = SlugRelatedField(read_only=True, source='name_text', slug_field='pt_br')
    section_key = CharField(read_only=True, source='section')
    section_name = SlugRelatedField(read_only=True, source='section_text', slug_field='pt_br')
    data_type = CharField(read_only=True)
    is_nullable = CharField(read_only=True)
    numeric_value_min = IntegerField(read_only=True)
    numeric_value_max = IntegerField(read_only=True)
    text_value_options = SlugRelatedField(read_only=True, many=True, slug_field='option_text__pt_br')

    class Meta:
        model = PlantTrait
        fields = [
            'key',
            'name',
            'section_key',
            'section_name',
            'data_type',
            'is_nullable',
            'numeric_value_min',
            'numeric_value_max',
            'text_value_options',
        ]
    

class PlantTraitValueSerializer(ModelSerializer):
    trait_key = SlugRelatedField(read_only=True, source='trait', slug_field='name')
    trait_name = SlugRelatedField(read_only=True, source='trait', slug_field='name_text__pt_br')
    section_key = SlugRelatedField(read_only=True, source='trait', slug_field='section')
    section_name = SlugRelatedField(read_only=True, source='trait', slug_field='section_text__pt_br')
    value = SerializerMethodField()

    def get_value(self, obj):
        value = obj.value
        data_type = obj.trait.data_type

        if data_type == 'int4range':
            min, max = json.loads(value)
            return {
                "type": "integer",
                "minimum": min,
                "maximum": max
            }
        elif data_type == 'numrange':
            min, max = json.loads(value)
            return {
                "type": "numeric",
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
            'content_status',
            'trait_key',
            'trait_name',
            'section_key',
            'section_name',
            'value',
            'source_id',
        ]

class ScientificNameSerializer(ModelSerializer):
    class Meta:
        model = PlantScientificName
        fields = [
            'name',
            'taxonomic_status',
            'plant_id',
        ]

class PlantScientificNameSerializer(ScientificNameSerializer):
    class Meta:
        model = PlantScientificName
        fields = [
            'name',
            'taxonomic_status',
        ]

class PopularNameSerializer(ModelSerializer):
    class Meta:
        model = PlantPopularName
        fields = [
            'name',
            'plant_id',
        ]

class PlantPopularNameSerializer(PopularNameSerializer):
    class Meta:
        model = PlantPopularName
        fields = [
            'name',
        ]

class PlantSerializer(ModelSerializer):
    def __init__(self,  *args, **kwargs):
        params = kwargs.pop('params', {})
        if params.get('with_scientific_names'):
            self.fields['scientific_names'] = SlugRelatedField(many=True, read_only=True, slug_field='name')
        if params.get('with_popular_names'):
            self.fields['popular_names'] = SlugRelatedField(many=True, read_only=True, slug_field='name')
        if params.get('with_trait_values'):
            self.fields['trait_values'] = PlantTraitValueSerializer(many=True, read_only=True, source='values')

        super().__init__(*args, **kwargs)

    class Meta:
        model = Plant
        fields = [
            'id',
            'accepted_scientific_name',
        ]
