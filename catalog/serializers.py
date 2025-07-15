from rest_framework.serializers import ModelSerializer, SlugRelatedField
from catalog.models import Plant, PlantPopularName, PlantScientificName

class PlantSerializer(ModelSerializer):    
    class Meta:
        model = Plant
        fields = [
            'id',
            'accepted_scientific_name',
        ]

class ScientificNameSerializer(ModelSerializer):
    plant = PlantSerializer(read_only=True)
    popular_names = SlugRelatedField(many=True, read_only=True, source='plant.popular_names', slug_field='name')

    class Meta:
        model = PlantScientificName
        fields = [
            'name',
            'taxonomic_status',
        ]

class PopularNameSerializer(ModelSerializer):
    plant = PlantSerializer(read_only=True)

    class Meta:
        model = PlantPopularName
        fields = [
            'name',
            'plant',
        ]

class PlantScientificNamesSerializer(PlantSerializer):
    scientific_names = SlugRelatedField(many=True, read_only=True, slug_field='name')

    class Meta(PlantSerializer.Meta):
        fields = PlantSerializer.Meta.fields + ['scientific_names']

