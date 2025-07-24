from rest_framework.serializers import Serializer, Field, CharField, BooleanField

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
