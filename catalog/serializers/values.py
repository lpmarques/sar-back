from rest_framework.serializers import CharField, IntegerField, ListField, Serializer

class NaturalOccurrenceRegionSerializer(Serializer):
    country = CharField(read_only=True, source='country__name_text__pt_br')
    state = CharField(read_only=True, source='state__code')
    biome = CharField(read_only=True, source='biome__name')
    vegetation_type = CharField(read_only=True, source='vegetation_type__name')
    plant_ids = ListField(read_only=True)
