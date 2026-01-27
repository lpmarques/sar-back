from django.db import transaction
from rest_framework.serializers import CharField, IntegerField, ModelSerializer, Serializer, SerializerMethodField, SlugRelatedField, ValidationError
from unidecode import unidecode
from catalog.models import Plant, NaturalOccurrenceRegion, PopularName, Taxon, Trait, TraitTextValueOption, TraitValue
from catalog.utils import md5_to_color, none_if_empty, string_to_md5
from core.models import Text
from core.serializers import ContentSerializer
from geography.models import Country, VegetationArea
from geography.serializers import BiomeSerializer, CountrySerializer, StateSerializer, VegetationTypeSerializer
import json
import re

pg_to_json_type = {
    'int4range': 'range',
    'numrange': 'range',
    'varchar[]': 'string[]',
    'varchar': 'string',
    'integer': 'number',
    'decimal': 'number',
    'boolean': 'boolean'
}

class TraitTextValueOptionSerializer(ModelSerializer):
    value = SlugRelatedField(read_only=True, source='value_text', slug_field='pt_br')
    description = SlugRelatedField(read_only=True, source='description_text', slug_field='pt_br')

    class Meta:
        model = TraitTextValueOption
        fields = [
            'value',
            'description',
        ]

class TraitSerializer(ModelSerializer):
    id = IntegerField(read_only=True)
    slug = CharField(read_only=True, source='name')
    name = SlugRelatedField(read_only=True, source='name_text', slug_field='pt_br')
    section_slug = CharField(read_only=True, source='section')
    section_name = SlugRelatedField(read_only=True, source='section_text', slug_field='pt_br')
    description = SlugRelatedField(read_only=True, source='description_text', slug_field='pt_br')
    type = SerializerMethodField()
    is_nullable = CharField(read_only=True)
    numeric_value_min = IntegerField(read_only=True)
    numeric_value_max = IntegerField(read_only=True)
    text_value_options = TraitTextValueOptionSerializer(read_only=True, many=True, source='trait_text_value_options')

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
            'description',
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
    trait_id = IntegerField()
    plant_id = IntegerField()

    def __init__(self,  *args, **kwargs):
        kwargs['content_type'] = "trait_value"

        super().__init__(*args, **kwargs)

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
        if value is None:
            raise ValidationError({'value': "Campo obrigatório."})

        try:
            trait = Trait.objects.denormalized().get(id=data.get('trait_id'))
        except Trait.DoesNotExist:
            raise ValidationError({'trait_id': "Não há traço cadastrado com esse id."})

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

        try:
            Plant.objects.get(id=data['plant_id'])
        except Plant.DoesNotExist:
            raise ValidationError({'plant_id': "Não há planta cadastrada com esse id."})

        matching_values = TraitValue.objects.filter(
            plant_id=data['plant_id'],
            trait_id=data['trait_id'],
            content__status__in=["accepted", "proposed"],
            value=data['value'],
        )
        if matching_values:
            raise ValidationError({'value': "Valor igual ao aceito ou a um valor já proposto para a mesma planta."})

        if trait.data_type in ["varchar", "varchar[]"]:
            values = value if trait.data_type == "varchar[]" else [value]
            if len(values) == 0:
                raise ValidationError({'value': "Valor não pode ser vazio."})

            options = [item.pt_br for item in trait.text_value_options.all()]
            for item in values:
                if item not in options:
                    raise ValidationError({
                        'value': f"Valor '{item}' inválido para o traço. Valores permitidos: {json.dumps(options)}"
                    })
        # TODO: replace below with json schema validation
        if trait.data_type == "number":
            if value >= trait.numeric_value_min and value <= trait.numeric_value_max:
                raise ValidationError(
                    {'value': f"Valor '{value}' fora do intervalo permitido para o traço: de {trait.numeric_value_min} até {trait.numeric_value_max}"}
                )
        if trait.data_type == "range":
            if (value[0] >= value[1]):
                raise ValidationError({'value': "O valor mínimo do intervalo não pode ser inferior ao valor máximo"})
            if (value[0] < trait.numericValueMin):
                raise ValidationError({'value': f"O valor mínimo está fora do intervalo permitido para o traço: de {trait.numeric_value_min} até {trait.numeric_value_max}"})
            if (value[1] > trait.numericValueMax):
                raise ValidationError({'value': f"O valor máximo está fora do intervalo permitido para o traço: de {trait.numeric_value_min} até {trait.numeric_value_max}"})
        
        return super().validate(data)

    def create(self, validated_data):
        with transaction.atomic():
            content = super().create(validated_data)
            
            trait_value = TraitValue.objects.create(
                content_id = content.id,
                plant_id = validated_data.get('plant_id'),
                trait_id = validated_data.get('trait_id'),
                value = validated_data.get('value'),
            )

            if self.trait.data_type in ["varchar", "varchar[]"]:
                trait_value.texts.add(*self.texts)

            return trait_value
        
    def update(self, trait_value, data):
        try:
            accepted_trait_value = TraitValue.objects.get(trait_id=trait_value.trait_id, plant_id=trait_value.plant_id)
        except TraitValue.DoesNotExist:
            pass

        with transaction.atomic():
            if accepted_trait_value:
                current_accepted_content = accepted_trait_value.content
                current_accepted_content['status'] = "rejected"
                current_accepted_content['rejector_id'] = data['content_acceptor_id']
                current_accepted_content.save()

            super().update(trait_value.content, data)

        return trait_value

    class Meta(ContentSerializer.Meta):
        model = TraitValue
        fields = [
            'content_id',
            'plant_id',
            'trait_id',
            'trait_slug',
            'trait_name',
            'section_slug',
            'section_name',
            'type',
            'value',
            'boundaries',
        ] + ContentSerializer.Meta.fields

class TraitValuePreviewSerializer(TraitValueSerializer):
    class Meta:
        model = TraitValue
        fields = [
            'content_id',
            'content_status',
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
        'species': r'^([A-Z][a-z]+)\s((?:x\s)?[a-z]+)$',
        'subspecies': r'^[a-z]{2,}$',
        'variety': r'^[a-z]{2,}$',
    }

    def __init__(self,  *args, **kwargs):
        kwargs['content_type'] = "taxon"

        super().__init__(*args, **kwargs)
    
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
        try:
            Plant.objects.get(id=data['plant_id'])
        except Plant.DoesNotExist:
            raise ValidationError({'plant_id': "Não há planta cadastrada com esse id."})
        
        if data['taxonomic_status'] not in Taxon.STATUS.values:
            raise ValidationError({'taxonomic_status': f"Valor '{data['taxonomic_status']}' inválido. Valores válidos: {Taxon.STATUS.values}."})
        
        for key, patt in self.patterns.items():
            if data[key] and not re.match(patt, data[key]):
                raise ValidationError({f'{key}': f"Valor '{data[key]} inválido. Deve ser compatível com a expressão regular '{patt}.'"})
        
        matching_accepted = Taxon.objects.select_related('content').filter(
            family=data['family'],
            genus=data['genus'],
            species=data['species'],
            subspecies=data['subspecies'],
            variety=data['variety'],
            taxonomic_status=data['taxonomic_status'],
            content__status__in=["accepted"],
        )
        if matching_accepted:
            raise ValidationError({'non_field_errors': "Taxonomia idêntica ao nome aceito ou sinônimo de uma planta já cadastrada."})
        
        matching_proposals = Taxon.objects.select_related('content').filter(
            family=data['family'],
            genus=data['genus'],
            species=data['species'],
            subspecies=data['subspecies'],
            variety=data['variety'],
            taxonomic_status=data['taxonomic_status'],
            plant_id=data['plant_id'],
            content__status__in=["proposed"],
        )
        if matching_proposals:
            raise ValidationError({'non_field_errors': "Taxonomia idêntica a uma das propostas para a mesma planta."})
        
        return super().validate(data)

    def create(self, validated_data):
        with transaction.atomic():
            content = super().create(validated_data)
            
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
        
    def update(self, taxon, data):
        if taxon.taxonomic_status == "accepted":
            try:
                accepted_taxon = Taxon.objects.get(plant_id=taxon.plant_id, taxonomic_status="accepted")
            except Taxon.DoesNotExist:
                pass

        with transaction.atomic():
            # reject current accepted taxon if existent
            if accepted_taxon:
                current_accepted_content = accepted_taxon.content
                current_accepted_content.status = "rejected"
                current_accepted_content.rejector_id = data['content_acceptor_id']
                current_accepted_content.save()

            # effectively accept proposed content
            super().update(taxon.content, data)

        if accepted_taxon:
            # recreate previous accepted taxon as synonym
            # separate transaction has to be opened to avoid eternal loop
            with transaction.atomic():
                previous_accepted_values = accepted_taxon.values()
                previous_accepted_values.update({
                    'taxonomic_status': 'synonym',
                    'source_id': taxon.content.source_id,
                    'content_proposer_id': taxon.content.proposer_id,
                    'content_proposer_comment': taxon.content.proposer_comment,
                })
                new_synonym_taxon = self.create(previous_accepted_values)

                # automatically accept the proposal, efectivelly reincluding the previous taxon as synonym
                self.update(new_synonym_taxon, data)

        return taxon

    class Meta:
        model = Taxon
        fields = [
            'content_id',
            'plant_id',
            'family',
            'genus',
            'species',
            'subspecies',
            'variety',
            'taxonomic_status',
        ] + ContentSerializer.Meta.fields

class TaxonPreviewSerializer(TaxonSerializer):
    class Meta:
        model = Taxon
        fields = [
            'content_id',
            'content_status',
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

    patterns = {
        'name': r'^[-a-z]+$',
    }

    def __init__(self,  *args, **kwargs):
        kwargs['content_type'] = "popular_name"

        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        data['name'] = none_if_empty(data.get('name',"").lower())
        
        return super().to_internal_value(data)

    def validate(self, data):
        try:
            Plant.objects.get(id=data['plant_id'])
        except Plant.DoesNotExist:
            raise ValidationError({'plant_id': "Não há planta cadastrada com esse id."})
        
        for key, patt in self.patterns.items():
            if data[key] and not re.match(patt, unidecode(data[key])):
                raise ValidationError({f'{key}': f"Valor '{data[key]}' incompatível com a expressão regular '{patt}.'"})
        
        matching_names = PopularName.objects.filter(
            name=data['name'],
            plant_id=data['plant_id'],
            content__status__in=["accepted", "proposed"],
        )
        if matching_names:
            raise ValidationError({'name': "Nome igual a um dos nomes aceitos ou propostos para a mesma planta."})
        
        return super().validate(data)

    def create(self, validated_data):
        with transaction.atomic():
            content = super().create(validated_data)
            
            return PopularName.objects.create(
                content_id = content.id,
                plant_id = validated_data['plant_id'],
                name = validated_data['name'],
            )

    class Meta(ContentSerializer.Meta):
        model = PopularName
        fields = [
            'content_id',
            'content_status',
            'plant_id',
            'name',
        ] + ContentSerializer.Meta.fields

class PopularNamePreviewSerializer(PopularNameSerializer):
    class Meta:
        model = PopularName
        fields = [
            'content_id',
            'content_status',
            'name',
        ]

class NaturalOccurrenceRegionSerializer(ContentSerializer):
    # read
    content_id = IntegerField(read_only=True)
    country = CountrySerializer(read_only=True)
    state = StateSerializer(read_only=True)
    biome = BiomeSerializer(read_only=True)
    vegetation_type = VegetationTypeSerializer(read_only=True)
    # write
    country_id = IntegerField(write_only=True)
    state_id = IntegerField(write_only=True, required=False)
    biome_id = IntegerField(write_only=True, required=False)
    vegetation_type_id = IntegerField(write_only=True, required=False)
    # both
    plant_id = IntegerField()

    def __init__(self,  *args, **kwargs):
        kwargs['content_type'] = "natural_occurrence_region"

        super().__init__(*args, **kwargs)

    def validate(self, data):
        # check conditionally required fields
        brazil = Country.objects.defer('area').get(name_text__pt_br='Brasil')
        if data.get('country_id') == brazil.id:
            missing_required_field_errors = []
            for field in ['state_id', 'biome_id', 'vegetation_type_id']:
                if not data.get(field):
                    missing_required_field_errors.append({f'{field}': "Campo obrigatório."})
            
            if missing_required_field_errors:
                raise ValidationError(missing_required_field_errors)

        # assert data refers to existing vegetation area
        if data.get('vegetation_type_id'):
            matching_vegetation_areas = VegetationArea.objects.defer('area').filter(
                country_id=data['country_id'],
                state_id=data.get('state_id'),
                biome_id=data.get('biome_id'),
                vegetation_type_id=data['vegetation_type_id'],
            )
            if len(matching_vegetation_areas) == 0:
                raise ValidationError({'non_field_errors': "Item inconsistente com as áreas de vegetação na base de dados."})

        # assert proposal uniqueness
        matching_occurrence_regions = NaturalOccurrenceRegion.objects.filter(
            plant_id=data['plant_id'],
            country_id=data['country_id'],
            state_id=data.get('state_id'),
            biome_id=data.get('biome_id'),
            vegetation_type_id=data.get('vegetation_type_id'),
            content__status__in=["accepted", "proposed"],
        )
        if matching_occurrence_regions:
            raise ValidationError({'non_field_errors': "Item igual a um dos aceitos ou propostos para a mesma planta."})
        
        return super().validate(data)

    def create(self, validated_data):
        with transaction.atomic():
            content = super().create(validated_data)
            
            return NaturalOccurrenceRegion.objects.create(
                content_id = content.id,
                plant_id = validated_data['plant_id'],
                country_id=validated_data['country_id'],
                state_id=validated_data.get('state_id'),
                biome_id=validated_data.get('biome_id'),
                vegetation_type_id=validated_data.get('vegetation_type_id'),
            )

    class Meta(ContentSerializer.Meta):
        model = NaturalOccurrenceRegion
        fields = [
            'content_id',
            'plant_id',
            'country',
            'state',
            'biome',
            'vegetation_type',
            'country_id',
            'state_id',
            'biome_id',
            'vegetation_type_id',
        ] + ContentSerializer.Meta.fields

class NaturalOccurrenceRegionPreviewSerializer(NaturalOccurrenceRegionSerializer):
    class Meta:
        model = NaturalOccurrenceRegion
        fields = [
            'content_id',
            'content_status',
            'country',
            'state',
            'biome',
            'vegetation_type',
        ]

class PlantCreationTaxonSerializer(Serializer):
    family = CharField(write_only=True)
    species = CharField(write_only=True)
    subspecies = CharField(write_only=True, required=False)
    variety = CharField(write_only=True, required=False)
    taxonomic_status = CharField(write_only=True)
    source_id = IntegerField(write_only=True)
    content_proposer_comment = CharField(write_only=True, required=False)

class PlantCreationPopularNameSerializer(Serializer):
    name = CharField(write_only=True)
    source_id = IntegerField(write_only=True)
    content_proposer_comment = CharField(write_only=True, required=False)

class PlantCreationSerializer(ContentSerializer):
    taxon = PlantCreationTaxonSerializer(write_only=True)
    popular_name = PlantCreationPopularNameSerializer(write_only=True)

    def __init__(self,  *args, **kwargs):
        kwargs['content_type'] = "plant"

        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        with transaction.atomic():
            # create plant
            content = super().create(validated_data)

            plant = Plant.objects.create(
                content_id = content.id,
                accepted_taxon_name = None,
                accepted_family_name = None,
                color_hex = validated_data.get('color_hex'),
            )

            # create taxon
            taxon_serializer = TaxonSerializer(data=dict(validated_data['taxon'], **{
                'taxonomic_status': 'accepted',
                'content_proposer_id': validated_data['content_proposer_id'],
                'plant_id': plant.id,
            }))
            if taxon_serializer.is_valid(raise_exception=True):
                taxon = taxon_serializer.save()

            # create popular_name
            popular_name_serializer = PopularNameSerializer(data=dict(validated_data['popular_name'], **{
                'content_proposer_id': validated_data['content_proposer_id'],
                'plant_id': plant.id,
            }))
            if popular_name_serializer.is_valid(raise_exception=True):
                popular_name = popular_name_serializer.save()

            # update plant with taxonomic data
            accepted_taxon_name = (
                f"{taxon.species}" +
                (f" subsp. {taxon.subspecies}" if taxon.subspecies else "") +
                (f" var. {taxon.variety}" if taxon.variety else "")
            )

            plant.accepted_taxon_name = accepted_taxon_name
            plant.accepted_family_name = taxon.family
            plant.color_hex = md5_to_color(string_to_md5(accepted_taxon_name))
            plant.save()

            return plant

    class Meta(ContentSerializer.Meta):
        model = Plant
        fields = [
            'taxon',
            'popular_name',
        ] + ContentSerializer.Meta.fields

class PlantSerializer(ContentSerializer):
    # read
    id = IntegerField(read_only=True)
    content_id = IntegerField(read_only=True)
    # both
    accepted_taxon_name = CharField(required=False)
    accepted_family_name = CharField(required=False)
    color_hex = CharField(required=False)

    def __init__(self,  *args, **kwargs):
        kwargs['content_type'] = "plant"

        params = kwargs.pop('params', {})
        if params.get('with_taxa'):
            self.fields['taxa'] = TaxonPreviewSerializer(many=True, read_only=True)
        if params.get('with_popular_names'):
            self.fields['popular_names'] = SlugRelatedField(many=True, read_only=True, slug_field='name')
        if params.get('with_trait_values'):
            self.fields['trait_values'] = TraitValuePreviewSerializer(many=True, read_only=True)
        if params.get('with_natural_occurrence_regions'):
            self.fields['natural_occurrence_regions'] = NaturalOccurrenceRegionPreviewSerializer(many=True, read_only=True)

        super().__init__(*args, **kwargs)

    class Meta(ContentSerializer.Meta):
        model = Plant
        fields = [
            'id',
            'content_id',
            'accepted_taxon_name',
            'accepted_family_name',
            'color_hex',
        ] + ContentSerializer.Meta.fields
