from rest_framework.serializers import CharField, DateTimeField, IntegerField, ListField, ModelSerializer, Serializer, SerializerMethodField, SlugRelatedField, ValidationError
from catalog.models import Plant, NaturalOccurrenceRegion, PopularName, Taxon, Trait, TraitValue
from core.models import Text
from core.serializers import ContentSerializer, SourceSerializer, UserPreviewSerializer
import json
import re

pg_to_json_type = {
    'int4range': 'range',
    'numrange': 'range',
    'varchar[]': 'string[]',
    'varchar': 'string',
    'integer': 'number',
    'boolean': 'boolean'
}

def none_if_empty(value: str):
    value = value.strip()
    if len(value) == 0:
        return None

    return value

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

class TraitValueSerializer(ContentSerializer):
    # read
    content_id = IntegerField(read_only=True)
    trait_slug = SlugRelatedField(read_only=True, source='trait', slug_field='name')
    trait_name = SlugRelatedField(read_only=True, source='trait', slug_field='name_text.pt_br')
    section_slug = SlugRelatedField(read_only=True, source='trait', slug_field='section')
    section_name = SlugRelatedField(read_only=True, source='trait', slug_field='section_text.pt_br')
    type = SerializerMethodField()
    boundaries = SerializerMethodField()
    # both
    value = CharField()
    trait_id = IntegerField(required=True)
    plant_id = IntegerField(required=True)

    def get_type(self, obj):
        return pg_to_json_type.get(obj.trait.data_type)

    def get_boundaries(self, obj):
        data_type = obj.trait.data_type

        if data_type in ['int4range', 'numrange', 'integer']:
            return [obj.trait.numeric_value_min, obj.trait.numeric_value_max]
        if data_type in ["varchar", "varchar[]"]:
            return [item.pt_br for item in obj.trait.text_value_options.all()]
        if data_type == "boolean":
            return [True, False]

        return []
    
    def to_representation(self, obj):
        data = super().to_representation(obj)

        data_type = obj.trait.data_type

        if data_type == "varchar[]":
            data['value'] = [item.pt_br for item in obj.texts.all()]
        elif data_type == "varchar":
            data['value'] = obj.texts.all()[0].pt_br
        else:
            data['value'] = json.loads(obj.value)

        return data
    
    def to_internal_value(self, data):
        value = data.get('value')
        if not value:
            raise ValidationError("O campo 'value' é obrigatório.")

        try:
            trait = Trait.objects.denormalized().get(id=data.get('trait_id'))
        except Trait.DoesNotExist:
            raise ValidationError("Não há traço cadastrado com esse id.")

        if trait.data_type == "varchar[]":
            self.texts = Text.objects.filter(**{'pt_br__in': value})
            data['value'] = json.dumps(sorted([text.en for text in self.texts]))
        elif trait.data_type == "varchar":
            self.texts = Text.objects.filter(**{'pt_br': value})
            data['value'] = self.texts[0].en
        else:
            data['value'] = json.dumps(value)

        self.trait = trait
        self.loaded_value = value

        return super().to_internal_value(data) # default method must run after custom so that it validates 'value' as string

    def validate(self, data):
        trait = self.trait
        value = self.loaded_value

        matching_values = TraitValue.objects.filter(
            plant_id=data['plant_id'],
            trait_id=data['trait_id'],
            content__status__in=["accepted", "proposed"],
            value=data['value'],
        )
        if matching_values:
            raise ValidationError("Valor igual ao aceito ou a um valor já proposto para a mesma planta.")

        if trait.data_type in ["varchar", "varchar[]"]:
            values = value if trait.data_type == "varchar[]" else [value]
            if len(values) == 0:
                raise ValidationError("Valor não pode ser vazio.")
            options = TraitSerializer(trait).data.get('text_value_options')
            for item in values:
                if item not in options:
                    raise ValidationError(
                        f"Valor '{item}' inválido para o traço. Valores permitidos: {json.dumps(options)}"
                    )
        if trait.data_type == "number":
            if value >= trait.numeric_value_min and value <= trait.numeric_value_max:
                raise ValidationError(
                    f"Valor '{value}' fora do intervalo permitido para o traço: de {trait.numeric_value_min} até {trait.numeric_value_max}"
                )
        if trait.data_type == "range":
            if (value[0] >= value[1]):
                raise ValidationError("O valor mínimo do intervalo não pode ser inferior ao valor máximo")
            if (value[0] < trait.numericValueMin):
                raise ValidationError(f"O valor mínimo está fora do intervalo permitido para o traço: de {trait.numeric_value_min} até {trait.numeric_value_max}")
            if (value[1] > trait.numericValueMax):
                raise ValidationError(f"O valor máximo está fora do intervalo permitido para o traço: de {trait.numeric_value_min} até {trait.numeric_value_max}")
        
        return data

    def create(self, validated_data):
        content = super().create(validated_data, "trait_value")
        
        trait_value = TraitValue.objects.create(
            content_id = content.id,
            plant_id = validated_data.get('plant_id'),
            trait_id = validated_data.get('trait_id'),
            value = validated_data.get('value'),
        )

        if self.trait.data_type in ["varchar", "varchar[]"]:
            trait_value.texts.add(*self.texts)

        return trait_value

    class Meta(ContentSerializer.Meta):
        model = TraitValue
        fields = ContentSerializer.Meta.fields + [
            'content_id',
            'content_status',
            'trait_id',
            'plant_id',
            'trait_slug',
            'trait_name',
            'section_slug',
            'section_name',
            'type',
            'value',
            'boundaries',
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

class TaxonSerializer(ContentSerializer):
    # read
    content_id = IntegerField(read_only=True)
    genus = CharField(read_only=True)
    # both
    family = CharField()
    species = CharField()
    subspecies = CharField(required=False)
    variety = CharField(required=False)
    taxonomic_status = CharField()
    plant_id = IntegerField()

    patterns = {
        'family': r'^[A-Z][a-z]+$',
        'genus': r'^[A-Z][a-z]+$',
        'species': r'^([A-Z][a-z]+)\s([a-z]{2,})$',
        'subspecies': r'^[a-z]{2,}$',
        'variety': r'^[a-z]{2,}$',
    }
    
    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        species_match = re.match(self.patterns['species'], data.get('species', ""))

        data['family'] = none_if_empty(data.get('family', "").capitalize())
        data['genus'] = species_match.group(1) if species_match else ""
        data['species'] = none_if_empty(data.get('species', "").capitalize())
        data['subspecies'] = none_if_empty(data.get('subspecies', "").lower())
        data['variety'] = none_if_empty(data.get('variety', "").lower())
        data['taxonomic_status'] = none_if_empty(data.get('taxonomic_status', "").lower())

        return data

    def validate(self, data):
        if data['taxonomic_status'] not in Taxon.STATUS.values:
            raise ValidationError(f"Campo 'taxonomic_status' inválido. Valores válidos: {Taxon.STATUS.values}.")
        
        for key, patt in self.patterns.items():
            if data[key] and not re.match(patt, data[key]):
                raise ValidationError(f"Campo '{key}' inválido. Valor deve ser compatível com a expressão regular '{patt}.'")
        
        matching_names = Taxon.objects.select_related('content').filter(
            family=data['family'],
            genus=data['genus'],
            species=data['species'],
            subspecies=data['subspecies'],
            variety=data['variety'],
            taxonomic_status=data['taxonomic_status'],
            plant_id=data['plant_id'],
            content__status__in=["accepted", "proposed"],
        )

        if matching_names:
            raise ValidationError("Taxonomia idêntica a uma das aceitas ou propostas para a mesma planta.")
        
        return data

    def create(self, validated_data):
        content = super().create(validated_data, "taxon")
        
        return Taxon.objects.create(
            content_id = content.id,
            plant_id = validated_data['plant_id'],
            family = validated_data['family'],
            genus = validated_data['genus'],
            species = validated_data['species'],
            subspecies = validated_data['subspecies'],
            variety = validated_data['variety'],
            taxonomic_status = validated_data['taxonomic_status'],
        )

    class Meta:
        model = Taxon
        fields = ContentSerializer.Meta.fields + [
            'content_id',
            'family',
            'genus',
            'species',
            'subspecies',
            'variety',
            'taxonomic_status',
            'plant_id',
        ]

class PlantTaxonSerializer(TaxonSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data.pop('plant_id', None)

        return data

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

class PopularNameSerializer(ContentSerializer):
    # read
    content_id = IntegerField(read_only=True)
    # both
    name = CharField()
    plant_id = IntegerField()

    def to_internal_value(self, data):
        data['name'] = none_if_empty(data.get('name',"").lower())
        
        return super().to_internal_value(data)

    def validate(self, data):
        matching_names = PopularName.objects.filter(
            name=data['name'],
            plant_id=data['plant_id'],
            content__status__in=["accepted", "proposed"],
        )
        if matching_names:
            raise ValidationError("Nome igual a um dos nomes aceitos ou propostos para a mesma planta.")
        
        return data

    def create(self, validated_data):
        content = super().create(validated_data, "popular_name")
        
        return PopularName.objects.create(
            content_id = content.id,
            plant_id = validated_data['plant_id'],
            name = validated_data['name'],
        )

    class Meta(ContentSerializer.Meta):
        model = PopularName
        fields = ContentSerializer.Meta.fields + [
            'content_id',
            'name',
            'plant_id',
        ]

class PlantPopularNameSerializer(PopularNameSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data.pop('plant_id', None)

        return data

class NaturalOccurrenceRegionSerializer(ContentSerializer):
    content_id = IntegerField(read_only=True)
    country = CharField(read_only=True, source='country.name_text.pt_br')
    state = CharField(read_only=True, source='state.code')
    biome = CharField(read_only=True, source='biome.name')
    vegetation_type = CharField(read_only=True, source='vegetation_type.name')

    class Meta(ContentSerializer.Meta):
        model = NaturalOccurrenceRegion
        fields = ContentSerializer.Meta.fields + [
            'content_id',
            'country',
            'state',
            'biome',
            'vegetation_type',
        ]

class PlantNaturalOccurrenceRegionSerializer(NaturalOccurrenceRegionSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data.pop('plant_id', None)

        return data

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

class PlantSerializer(ContentSerializer):
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
