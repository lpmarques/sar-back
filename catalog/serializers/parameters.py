from rest_framework.serializers import Serializer, Field, CharField, BooleanField

class StringListField(Field):
    def __init__(self, separator=",", *args, **kwargs):
        self.separator = separator
        super().__init__(*args, **kwargs)

    def to_internal_value(self, value):
        return self.separator.join(value) if value else None
    
    def to_representation(self, value):
        return value.split(self.separator) if value else None

class ScientificNameParamsSerializer(Serializer):
    content_status__in = StringListField(required=False, allow_null=False, source='status')
    taxonomic_status = CharField(required=False, allow_blank=False)

class PopularNameParamsSerializer(Serializer):
    content_status__in = StringListField(required=False, allow_null=False, source='status')

class NaturalOccurrenceRegionParamsSerializer(Serializer):
    country__name_text__pt_br = CharField(required=False, allow_blank=False, source='country') # TODO: match with slug field
    state__code = CharField(required=False, allow_null=False, source='state') # TODO: match with slug field
    biome__name = CharField(required=False, allow_blank=False, source='biome') # TODO: match with slug field
    vegetation_type__name = CharField(required=False, allow_blank=False, source='vegetation_type') # TODO: match with slug field

class TraitParamsSerializer(Serializer):
    section__in = StringListField(required=False, allow_null=False, source='section_slugs')

class PlantTraitValueParamsSerializer(Serializer):
    content_status__in = StringListField(required=False, allow_null=False, source='status')
    trait__name__in = StringListField(required=False, allow_null=False, source='trait_slugs')
    trait__section__in = StringListField(required=False, allow_null=False, source='section_slugs')

class PlantParamsSerializer(Serializer):
    content_status__in = StringListField(required=False, allow_null=False, source='plant_status')

    with_scientific_names = BooleanField(required=False, allow_null=False)
    with_popular_names = BooleanField(required=False, allow_null=False)
    with_trait_values = BooleanField(required=False, allow_null=False)
    with_natural_occurrence_regions = BooleanField(required=False, allow_null=False)
    scientific_names_status = CharField(required=False, allow_blank=False)
    scientific_names_taxonomic_status = CharField(required=False, allow_blank=False)
    popular_names_status = CharField(required=False, allow_blank=False)
    trait_values_status = CharField(required=False, allow_blank=False)
    trait_values_trait_slugs = CharField(required=False, allow_null=False)
    trait_values_section_slugs = CharField(required=False, allow_null=False)
    natural_occurrence_regions_status = CharField(required=False, allow_blank=False)
    # TODO: add natural_occurrence_regions filter params
