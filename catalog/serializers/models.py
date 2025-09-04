from rest_framework.serializers import CharField, DateTimeField, IntegerField, ListField, ModelSerializer, Serializer, SerializerMethodField, SlugRelatedField, ValidationError
from catalog.models import Plant, NaturalOccurrenceRegion, PopularName, Taxon, Trait, TraitValue
from core.models import Content, Text
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
    text_value_options = SlugRelatedField(read_only=True, many=True, slug_field='pt_br')

    def get_type(self, obj):
        return pg_to_json_type.get(obj.data_type)

    class Meta:
        model = Trait
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
    content_id = IntegerField(read_only=True)
    trait_slug = SlugRelatedField(read_only=True, source='trait', slug_field='name')
    trait_name = SlugRelatedField(read_only=True, source='trait', slug_field='name_text.pt_br')
    section_slug = SlugRelatedField(read_only=True, source='trait', slug_field='section')
    section_name = SlugRelatedField(read_only=True, source='trait', slug_field='section_text.pt_br')
    type = SerializerMethodField()
    boundaries = SerializerMethodField()
    content_status = CharField(read_only=True, source='content.status')
    content_proposer = UserPreviewSerializer(read_only=True, source='content.proposer')
    source = SourceSerializer(read_only=True, source='content.source')
    endorsements = IntegerField(read_only=True, source='content.endorsements')
    proposed_at = DateTimeField(read_only=True, source='content.proposed_at')
    accepted_at = DateTimeField(read_only=True, source='content.accepted_at')
    rejected_at = DateTimeField(read_only=True, source='content.rejected_at')
    # write
    source_id = IntegerField(write_only=True, required=True)
    content_proposer_id = IntegerField(write_only=True, required=True)
    content_proposer_comment = CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    # both
    value = WritableSerializerMethodField(setter_method_name='set_value_field')
    trait_id = IntegerField(required=True)
    plant_id = IntegerField(required=True)

    def get_type(self, obj):
        return pg_to_json_type.get(obj.trait.data_type)

    def get_value(self, obj):
        value = obj.value
        data_type = obj.trait.data_type

        if data_type == "varchar[]":
            return [item.pt_br for item in obj.texts.all()]
        if data_type == "varchar":
            return obj.texts.all()[0].pt_br

        return json.loads(value)

    def get_boundaries(self, obj):
        data_type = obj.trait.data_type

        if data_type in ['int4range', 'numrange', 'integer']:
            return [obj.trait.numeric_value_min, obj.trait.numeric_value_max]
        if data_type in ["varchar", "varchar[]"]:
            return [item.pt_br for item in obj.trait.text_value_options.all()]
        if data_type == "boolean":
            return [True, False]

        return []

    def set_value_field(self, value): # called before validation
        return value

    def value_to_string_value(self, value): # called before writing
        if self.trait.data_type in ['int4range', 'numrange']:
            return json.dumps([value.get('minimum'), value.get('maximum')])
        if self.trait.data_type in ["varchar", "varchar[]"]:
            values = value if self.trait.data_type == "varchar[]" else [value]
            texts = Text.objects.filter(**{'pt_br__in': values})
            return json.dumps(sorted([text.en for text in texts]))

        return json.dumps(value)

    def validate(self, data):
        value = data.get('value')

        try:
            self.trait = Trait.objects.denormalized().get(id=data.get('trait_id'))
        except Trait.DoesNotExist:
            raise ValidationError("Traço inexistente.")

        matching_values = TraitValue.objects.filter(
            plant_id=data['plant_id'],
            trait_id=self.trait.id,
            content__status__in=["accepted", "proposed"],
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

        content = Content.objects.create(
            status = 'proposed',
            source_id = validated_data.get('source_id'),
            proposer_id = validated_data.get('content_proposer_id'),
            proposer_comment = validated_data.get('content_proposer_comment'),
        )
        
        trait_value = TraitValue.objects.create(
            content_id = content.id,
            plant_id = validated_data.get('plant_id'),
            trait_id = validated_data.get('trait_id'),
            value = self.value_to_string_value(value),
        )

        if self.trait.data_type in ["varchar", "varchar[]"]:
            list = value if self.trait.data_type == "varchar[]" else [value]
            texts = Text.objects.filter(**{'pt_br__in': list})
            trait_value.texts.add(*texts)

        return trait_value

    class Meta:
        model = TraitValue
        fields = [
            'content_id',
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
            'content_proposer',
            'content_proposer_id',
            'content_proposer_comment',
            'endorsements',
            'proposed_at',
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
        model = TraitValue
        fields = [
            'content_id',
            'trait_slug',
            'trait_name',
            'type',
            'value',
        ]

class TaxonSerializer(ModelSerializer):
    content_status = CharField(source='content.status')

    class Meta:
        model = Taxon
        fields = [
            'content_id',
            'family',
            'genus',
            'species',
            'subspecies',
            'variety',
            'taxonomic_status',
            'content_status',
            'plant_id',
        ]

class PlantTaxonSerializer(TaxonSerializer):
    content_proposer = UserPreviewSerializer(source='content.proposer')
    endorsements = IntegerField(source='content.endorsements')
    source = SourceSerializer(source='content.source')
    proposed_at = DateTimeField(read_only=True, source='content.proposed_at')
    accepted_at = DateTimeField(read_only=True, source='content.accepted_at')
    rejected_at = DateTimeField(read_only=True, source='content.rejected_at')

    class Meta:
        model = Taxon
        fields = [
            'content_id',
            'family',
            'genus',
            'species',
            'subspecies',
            'variety',
            'taxonomic_status',
            'content_status',
            'content_proposer',
            'endorsements',
            'source',
            'proposed_at',
            'accepted_at',
            'rejected_at',
        ]

class PlantTaxonPreviewSerializer(PlantTaxonSerializer):
    class Meta:
        model = Taxon
        fields = [
            'content_id',
            'family',
            'genus',
            'species',
            'subspecies',
            'variety',
            'taxonomic_status',
        ]

class PopularNameSerializer(ModelSerializer):
    content_status = CharField(read_only=True, source='content.status')

    class Meta:
        model = PopularName
        fields = [
            'content_id',
            'name',
            'content_status',
            'plant_id',
        ]

class PlantPopularNameSerializer(PopularNameSerializer):
    content_proposer = UserPreviewSerializer(source='content.proposer')
    endorsements = IntegerField(source='content.endorsements')
    source = SourceSerializer(source='content.source')
    proposed_at = DateTimeField(read_only=True, source='content.proposed_at')
    accepted_at = DateTimeField(read_only=True, source='content.accepted_at')
    rejected_at = DateTimeField(read_only=True, source='content.rejected_at')
    
    class Meta:
        model = PopularName
        fields = [
            'content_id',
            'name',
            'content_status',
            'content_proposer',
            'endorsements',
            'source',
            'proposed_at',
            'accepted_at',
            'rejected_at',
        ]

class NaturalOccurrenceRegionSerializer(Serializer):
    country = CharField(read_only=True, source='country.name_text.pt_br')
    state = CharField(read_only=True, source='state.code')
    biome = CharField(read_only=True, source='biome.name')
    vegetation_type = CharField(read_only=True, source='vegetation_type.name')
    plant_ids = ListField(read_only=True)

class PlantNaturalOccurrenceRegionSerializer(ModelSerializer):
    country = SlugRelatedField(read_only=True, slug_field='name_text__pt_br')
    state = SlugRelatedField(read_only=True, slug_field='code')
    biome = SlugRelatedField(read_only=True, slug_field='name')
    vegetation_type = SlugRelatedField(read_only=True, slug_field='name')
    content_status = CharField(read_only=True, source='content.status')
    content_proposer = UserPreviewSerializer(read_only=True, source='content.proposer')
    source = SourceSerializer(read_only=True, source='content.source')
    proposed_at = DateTimeField(read_only=True, source='content.proposed_at')
    accepted_at = DateTimeField(read_only=True, source='content.accepted_at')
    rejected_at = DateTimeField(read_only=True, source='content.rejected_at')

    class Meta:
        model = NaturalOccurrenceRegion
        fields = [
            'content_id',
            'country',
            'state',
            'biome',
            'vegetation_type',
            'content_status',
            'content_proposer',
            'source',
            'proposed_at',
            'accepted_at',
            'rejected_at',
        ]

class PlantNaturalOccurrenceRegionPreviewSerializer(PlantNaturalOccurrenceRegionSerializer):
    class Meta:
        model = NaturalOccurrenceRegion
        fields = [
            'content_id',
            'country',
            'state',
            'biome',
            'vegetation_type',
        ]

class PlantSerializer(ModelSerializer):
    content_status = CharField(read_only=True, source='content.status')
    proposed_at = DateTimeField(read_only=True, source='content.proposed_at')
    accepted_at = DateTimeField(read_only=True, source='content.accepted_at')
    rejected_at = DateTimeField(read_only=True, source='content.rejected_at')

    def __init__(self,  *args, **kwargs):
        params = kwargs.pop('params', {})
        if params.get('with_taxa'):
            self.fields['taxa'] = PlantTaxonPreviewSerializer(many=True, read_only=True)
        if params.get('with_popular_names'):
            self.fields['popular_names'] = SlugRelatedField(many=True, read_only=True, slug_field='name')
        if params.get('with_trait_values'):
            self.fields['trait_values'] = PlantTraitValuePreviewSerializer(many=True, read_only=True)
        if params.get('with_natural_occurrence_regions'):
            self.fields['natural_occurrence_regions'] = PlantNaturalOccurrenceRegionPreviewSerializer(many=True, read_only=True)

        super().__init__(*args, **kwargs)

    class Meta:
        model = Plant
        fields = [
            'id',
            'content_id',
            'accepted_taxon_name',
            'accepted_family_name',
            'content_status',
            'proposed_at',
            'accepted_at',
            'rejected_at',
        ]
