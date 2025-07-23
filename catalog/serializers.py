from rest_framework.serializers import Serializer, BooleanField, CharField, DecimalField, IntegerField, ListField, ModelSerializer, SerializerMethodField, SlugRelatedField
from catalog.models import Plant, PlantPopularName, PlantScientificName, PlantValue
import json

class PlantQueryParamsSerializer(Serializer):
    scientific_names = BooleanField(required=False, allow_null=False)
    scientific_names_status = CharField(required=False, allow_blank=False)
    scientific_names_taxonomic_status = CharField(required=False, allow_blank=False)
    popular_names = BooleanField(required=False, allow_null=False)
    popular_names_status = CharField(required=False, allow_blank=False)
    trait_values = BooleanField(required=False, allow_null=False)
    trait_values_status = CharField(required=False, allow_blank=False)
    trait_values_trait_keys = SerializerMethodField(required=False, allow_null=False)

    def get_trait_values_trait_keys(self, obj):
        trait_values_trait_keys = obj.get('trait_values_trait_keys')
        return trait_values_trait_keys.split(',') if trait_values_trait_keys else None

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

class PopularNameSerializer(ModelSerializer):
    class Meta:
        model = PlantPopularName
        fields = [
            'name',
            'plant_id',
        ]

class PlantSerializer(ModelSerializer):
    def __init__(self,  *args, **kwargs):
        # import pdb; pdb.set_trace()
        params = kwargs.pop('params', {})
        if params.get('scientific_names'):
            self.fields['scientific_names'] = SlugRelatedField(many=True, read_only=True, slug_field='name')
        if params.get('popular_names'):
            self.fields['popular_names'] = SlugRelatedField(many=True, read_only=True, slug_field='name')
        if params.get('trait_values'):
            self.fields['trait_values'] = PlantTraitValueSerializer(many=True, read_only=True, source='values')

        super().__init__(*args, **kwargs)

    class Meta:
        model = Plant
        fields = [
            'id',
            'accepted_scientific_name',
        ]
