from rest_framework.serializers import Serializer, Field, CharField, BooleanField, IntegerField
from core.serializers import StringListField

class TaxonParamsSerializer(Serializer):
    content_id = IntegerField(required=False, allow_null=False)
    content__status__in = StringListField(required=False, allow_null=False, source='status')
    taxonomic_status = CharField(required=False, allow_blank=False)

class PopularNameParamsSerializer(Serializer):
    content_id = IntegerField(required=False, allow_null=False)
    content__status__in = StringListField(required=False, allow_null=False, source='status')

class NaturalOccurrenceRegionParamsSerializer(Serializer):
    content_id = IntegerField(required=False, allow_null=False)
    content__status__in = StringListField(required=False, allow_null=False, source='status')
    country__name_text__pt_br = CharField(required=False, allow_blank=False, source='country')
    state__code = CharField(required=False, allow_null=False, source='state')
    biome__name = CharField(required=False, allow_blank=False, source='biome')
    vegetation_type__name = CharField(required=False, allow_blank=False, source='vegetation_type')

class TraitParamsSerializer(Serializer):
    name__in = StringListField(required=False, allow_null=False, source='trait_slugs')
    section__in = StringListField(required=False, allow_null=False, source='section_slugs')

class TraitValueParamsSerializer(Serializer):
    content_id = IntegerField(required=False, allow_null=False)
    content__status__in = StringListField(required=False, allow_null=False, source='status')
    trait__name__in = StringListField(required=False, allow_null=False, source='trait_slugs')
    trait__section__in = StringListField(required=False, allow_null=False, source='section_slugs')

class PlantParamsSerializer(Serializer):
    plant_content_id = IntegerField(required=False, allow_null=False, source='content_id')
    plant_content__status__in = StringListField(required=False, allow_null=False, source='status')

    with_taxa = BooleanField(required=False, allow_null=False)
    with_popular_names = BooleanField(required=False, allow_null=False)
    with_trait_values = BooleanField(required=False, allow_null=False)
    with_natural_occurrence_regions = BooleanField(required=False, allow_null=False)
    taxa_status = CharField(required=False, allow_blank=False)
    taxa_taxonomic_status = CharField(required=False, allow_blank=False)
    popular_names_status = CharField(required=False, allow_blank=False)
    trait_values_status = CharField(required=False, allow_blank=False)
    trait_values_trait_slugs = CharField(required=False, allow_null=False)
    trait_values_section_slugs = CharField(required=False, allow_null=False)
    natural_occurrence_regions_status = CharField(required=False, allow_blank=False)
    # TODO: add natural_occurrence_regions filter params
