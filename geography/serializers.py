from rest_framework.serializers import CharField, IntegerField, ModelSerializer, Serializer, SlugRelatedField
from geography.models import Biome, Country, Municipality, State, VegetationType

class CountrySerializer(ModelSerializer):
    name = SlugRelatedField(read_only=True, source='name_text', slug_field='pt_br')

    class Meta:
        model = Country
        fields = [
            'id',
            'name',
        ]

class StateParamsSerializer(Serializer):
    vegetation_areas__biome_id = CharField(required=False, allow_blank=False, source='biome_id')
    
class StateSerializer(ModelSerializer):
    name = CharField(read_only=True)
    code = CharField(read_only=True)
    country_id = IntegerField(read_only=True)

    class Meta:
        model = State
        fields = [
            'id',
            'name',
            'code',
            'country_id',
        ]

class MunicipalitySerializer(ModelSerializer):
    name = CharField(read_only=True)
    state_id = IntegerField(read_only=True)
    country_id = IntegerField(read_only=True)

    class Meta:
        model = Municipality
        fields = [
            'id',
            'name',
            'state_id',
            'country_id',
        ]

class BiomeParamsSerializer(Serializer):
    vegetation_areas__state_id = CharField(required=False, allow_blank=False, source='state_id')

class BiomeSerializer(ModelSerializer):
    name = CharField(read_only=True)
    country_id = IntegerField(read_only=True)

    class Meta:
        model = Biome
        fields = [
            'id',
            'name',
            'country_id',
        ]

class VegetationTypeParamsSerializer(Serializer):
    vegetation_areas__state_id = CharField(required=False, allow_blank=False, source='state_id')
    vegetation_areas__biome_id = CharField(required=False, allow_blank=False, source='biome_id')

class VegetationTypeSerializer(ModelSerializer):
    name = CharField(read_only=True)
    country_id = IntegerField(read_only=True)

    class Meta:
        model = VegetationType
        fields = [
            'id',
            'name',
            'country_id',
        ]
