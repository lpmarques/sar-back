# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.


from django.apps import apps
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Now
from py_mini_racer import MiniRacer
from jsonschema import FormatChecker, validate
from rest_framework.serializers import BooleanField, CharField, ChoiceField, DateTimeField, DecimalField, IntegerField, JSONField, ModelSerializer, Serializer, SerializerMethodField, ValidationError
from rest_framework_gis.fields import GeometryField
from catalog.models import InvasionRiskRegion
from catalog.serializers.models import PlantPreviewSerializer, PlantSerializer
from core.serializers import UserPreviewSerializer
from core.models import Content, Text
from core.utils import full_name
from geography.models import Biome, Country, Municipality, State, VegetationArea
from geography.serializers import BiomeSerializer, CountrySerializer, MunicipalitySerializer, StateSerializer, VegetationTypeSerializer
from agroforestry.models import Cropping, CroppingPattern, CroppingPatternCrop, CroppingPatternRow, Farm, Field, Function, Site, SiteTrait, SiteTraitTextValueOption, SiteTraitValue
from agroforestry.utils import hash_object, none_if_empty, none_if_nan
from typing import List, Union
import hashlib
import json

class FunctionSerializer(ModelSerializer):
    class Meta:
        model = Function
        fields = [
            'name',
            'input_schema',
            'body',
            'return_schema',
        ]

class SiteTraitTextValueOptionSerializer(ModelSerializer):
    value = CharField(read_only=True, source='value_text.pt_br')
    description = CharField(read_only=True, source='description_text.pt_br')

    class Meta:
        model = SiteTraitTextValueOption
        fields = [
            'value',
            'description',
        ]
        
class TraitsFitnessSerializer(Serializer):
    plant_trait_slug = CharField()
    fitness_score = IntegerField()

class SitePlantFitnessSerializer(Serializer):
    plant_id = IntegerField()
    accepted_taxon_name = CharField()
    color_hex = CharField()
    is_native = BooleanField()
    is_invasive = BooleanField()
    eicat_category = ChoiceField(choices=InvasionRiskRegion.EICAT)
    # traits_fitness = TraitsFitnessSerializer(many=True)
    fitness_score = IntegerField()
    nativity_score = IntegerField()
    
    invasion_risk_penalties = {
        InvasionRiskRegion.EICAT.MT.value: -25,
        InvasionRiskRegion.EICAT.MJ.value: -50,
        InvasionRiskRegion.EICAT.MV.value: -100
    }

    def __init__(self, *args, **kwargs):
        functions = FunctionSerializer(Function.objects.all(), many=True)
        
        self.js_ctx = MiniRacer()
        self.js_ctx.eval('\n'.join([f['body'] for f in functions.data]))

        super().__init__(*args, **kwargs)

    def render_function_input(self, template, values):
        return { k: values[v] if v in values.keys() else v for k, v in template.items() }

    def parse_plant_trait_value(self, value, data_type): # TODO: somewhat repeated code: try moving to static method in trait serializer
        if data_type == "varchar[]":
            return value
        elif data_type == "varchar":
            return value[0]

        return json.loads(value)

    def parse_site_trait_value(self, value, schema): # TODO: somewhat repeated code: try moving to static method in trait serializer
        if schema['type'] == "array" and schema['items']['type'] == "string":
            return value
        elif schema['type'] == "string":
            return value[0]

        return json.loads(value)

    def parse_values(self, fitting):
        values = {
            '{plant_trait}': self.parse_plant_trait_value(fitting['plant_trait_value'], fitting['plant_trait_type']),
            '{site_trait}': self.parse_site_trait_value(fitting['site_trait_value'], fitting['site_trait_schema']),
        }

        if fitting['fitting_pre_transforms']:
            for prop, transform in fitting['fitting_pre_transforms'].items():
                values[f'{{{prop}}}'] = self.js_ctx.call(
                    transform['function'],
                    self.render_function_input(transform['input'], values)
                )
            
        return values

    def calc_traits_fitness_score(self, fitting):
        values = self.parse_values(fitting)
        function_input = self.render_function_input(fitting['fitting_function_input'], values)

        score = self.js_ctx.call(
            fitting['fitting_function_name'],
            function_input
        )
        return score
    
    def calc_plant_nativity_score(self, is_native, eicat_category=None):
        if eicat_category:
            return self.invasion_risk_penalties[eicat_category]
        if is_native:
            return 10

        return 0

    def to_representation(self, df):
        data = dict(zip(
            df.index.names,
            [none_if_nan(value) for value in df.index.to_list()[0]]
        )) # extract plant data from dataframe index
        df.reset_index(drop=True, inplace=True)

        data['fitness_score'] = sum(df.apply(func=self.calc_traits_fitness_score, axis=1))
        data['nativity_score'] = self.calc_plant_nativity_score(data['is_native'], data['eicat_category'])

        return super().to_representation(data)
    
    class Meta(PlantSerializer.Meta):
        fields = [
            'plant_id',
            'accepted_taxon_name',
            'color_hex',
            'is_native',
            'is_invasive',
            'eicat_category',
            'fitness_score',
            'nativity_score',
            # 'traits_fitness',
        ]

class SiteTraitSerializer(ModelSerializer):
    slug = CharField(read_only=True, source='name')
    name = CharField(read_only=True, source='name_text.pt_br')
    section_slug = CharField(read_only=True, source='section')
    section_name = CharField(read_only=True, source='section_text.pt_br')
    description = CharField(read_only=True, source='description_text.pt_br')
    slug = CharField(read_only=True, source='name')
    schema = JSONField(read_only=True)
    position = IntegerField(read_only=True)
    is_nullable = BooleanField(read_only=True)
    text_value_options = SiteTraitTextValueOptionSerializer(read_only=True, many=True, source='site_trait_text_value_options')

    class Meta:
        model = SiteTrait
        fields = [
            'id',
            'slug',
            'name',
            'section_slug',
            'section_name',
            'description',
            'schema',
            'position',
            'is_nullable',
            'text_value_options',
        ]

class SiteTraitValueSerializer(ModelSerializer):
    # both
    trait_id = IntegerField()
    # read
    trait_slug = CharField(read_only=True, source='trait.name')
    trait_name = CharField(read_only=True, source='trait.name_text.pt_br')
    section_slug = CharField(read_only=True, source='trait.section')
    section_name = CharField(read_only=True, source='trait.section_text.pt_br')
    schema = JSONField(read_only=True, source='trait.schema')
    
    def to_representation(self, obj):
        data = super().to_representation(obj)

        schema = obj.trait.schema

        if schema['type'] == "array" and schema['items']['type'] == "string":
            data['value'] = [item.pt_br for item in obj.texts.all()]
        elif schema['type'] == "string":
            data['value'] = obj.texts.all()[0].pt_br
        else:
            data['value'] = json.loads(obj.value)

        return data
    
    @staticmethod
    def get_value_texts(trait: SiteTrait, value) -> List[Text]:
        if trait.schema['type'] == "array" and trait.schema['items']['type'] == "string":
            return Text.objects.filter(**{'pt_br__in': value})
        elif trait.schema['type'] == "string":
            return Text.objects.filter(**{'pt_br': value})

        return []
    
    def to_internal_value(self, data):
        value = data.get('value')

        try:
            trait = SiteTrait.objects.denormalized().get(id=data.get('trait_id'))
        except SiteTrait.DoesNotExist:
            raise ValidationError({'trait_id': "Não há traço cadastrado com esse id."})

        self.texts = self.get_value_texts(trait, value)
        if trait.schema['type'] == "array" and trait.schema['items']['type'] == "string":
            data['value'] = json.dumps(sorted([text.en for text in self.texts]))
        elif trait.schema['type'] == "string":
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
            validate(value, trait.schema, format_checker=FormatChecker())
        except Exception as e:
            raise ValidationError({'value': f"Valor inválido para o traço '{trait.name_text.pt_br}' (trait_id: {trait.id}): {e}"})
        
        return data

    class Meta:
        model = SiteTraitValue
        fields = [
            'id',
            'trait_id',
            'trait_slug',
            'trait_name',
            'section_slug',
            'section_name',
            'schema',
            'value',
        ]

class DetachedSiteTraitValueSerializer(SiteTraitValueSerializer):
    site_id = IntegerField()

    def validate(self, data):
        trait = self.trait
        instance_id = self.instance.id if self.instance else 0

        try:
            self.site = Site.objects.get(id=data['site_id'])
        except Site.DoesNotExist:
            raise ValidationError({'site_id': "Não há local cadastrado com esse id."})
        
        active_trait_value = SiteTraitValue.objects.active().filter(
            ~Q(id=instance_id),
            site_id=self.site.id,
            trait_id=trait.id,
        )
        if active_trait_value:
            raise ValidationError({'non_field_errors': f"Já existe um valor do traço '{trait.name_text.pt_br}' (trait_id: {trait.id}) para esse local (site_id: {self.site.id})."})
        
        return super().validate(data)

    def create(self, validated_data):
        trait = self.trait
        texts = self.texts
        
        with transaction.atomic():
            trait_value = SiteTraitValue.objects.create(
                site_id = validated_data['site_id'],
                trait_id = validated_data['trait_id'],
                value = validated_data['value'],
            )

            value_type = trait.schema['type']
            if value_type == "string" or value_type == "array" and trait.schema['items']['type'] == "string":
                trait_value.texts.add(*texts)

            return trait_value

    def update(self, trait_value, validated_data):
        trait = self.trait
        texts = self.texts

        with transaction.atomic():
            value_type = trait.schema['type']
            if trait_value.value != validated_data['value'] and (
                value_type == "string" or value_type == "array" and trait.schema['items']['type'] == "string"
            ):
                trait_value.texts.clear()
                trait_value.texts.add(*texts)

            trait_value.site_id = validated_data['site_id']
            trait_value.trait_id = validated_data['trait_id']
            trait_value.value = validated_data['value']
            trait_value.save()

            return trait_value

    class Meta(SiteTraitValueSerializer.Meta):
        fields = SiteTraitValueSerializer.Meta.fields + [
            'site_id',
        ]


class SiteSerializer(ModelSerializer):
    # read
    area_m2 = SerializerMethodField()
    country = CountrySerializer(read_only=True, source='site.country')
    state = StateSerializer(read_only=True, source='site.state')
    municipality = MunicipalitySerializer(read_only=True, source='site.municipality')
    biome = BiomeSerializer(read_only=True, source='site.biome')
    vegetation_type = VegetationTypeSerializer(read_only=True, source='site.vegetation_type')
    created_at = DateTimeField(read_only=True, source='site.created_at')
    # write
    municipality_id = IntegerField(write_only=True, allow_null=True, required=False)
    # both
    location = GeometryField(required=False, source='site.location')
    polygon = GeometryField(required=False, source='site.polygon')
    trait_values = SiteTraitValueSerializer(many=True, source='site.trait_values')
    
    def __init__(self,  *args, **kwargs):
        self.site_type = kwargs.pop('site_type')

        super().__init__(*args, **kwargs)

    def get_area_m2(self, obj):
        if hasattr(obj, "area"):
            return round(obj.area.sq_m)
        
        return None
    
    def georep_to_geos(self, rep: Union[dict, str]):
        if not rep:
            return None
        if isinstance(rep, dict):
            rep = json.dumps(rep)

        return GEOSGeometry(rep)
    
    def to_internal_value(self, data):
        # traits and texts data must be recovered after nested serializer processing
        if data.get('trait_values'):
            self.traits = [
                SiteTrait.objects.denormalized().get(id=trait_value.get('trait_id')) for trait_value in data['trait_values']
            ]
            self.trait_values_texts = [
                SiteTraitValueSerializer.get_value_texts(trait, trait_value['value']) for trait, trait_value in zip(self.traits, data['trait_values'])
            ]

        data = super().to_internal_value(data)
        site_data = data.pop('site')

        return dict(**data, **site_data) # revert site fields nesting by default method

    def validate(self, data):
        if 'location' not in data and 'polygon' not in data:
            raise ValidationError({'non_field_errors': 'É obrigatório passar o campo location ou o campo polygon.'})
        if 'location' in data and 'polygon' in data:
            raise ValidationError({'non_field_errors': 'Somente um dos campos "location" e "polygon" deve ser passado.'})
        
        try:
            data['location'] = self.georep_to_geos(data.get('location'))
            assert data['location'] is None or data['location'].geom_type == 'Point'
        except:
            raise ValidationError({'location': 'Valor precisa ser wkt ou geojson de geometria do tipo Point.'})
        try:
            data['polygon'] = self.georep_to_geos(data.get('polygon'))
            assert data['polygon'] is None or data['polygon'].geom_type == 'Polygon'
        except:
            raise ValidationError({'polygon': 'Valor precisa ser wkt ou geojson de geometria do tipo Polygon.'})
        
        data['location'] = data['location'] or data['polygon'].centroid

        country = Country.objects.filter(area__contains=data['location']).first()
        if not country:
            raise ValidationError({
                'non_field_errors': (
                    'As coordenadas passadas em location ou polygon não correspondem a terra firme.'
                    'Certifique-se de utilizar o CRS WGS 84 (SRID 4326).'
                )
            })
        
        state = State.objects.filter(country_id=country.id, area__contains=data['location']).first()
        biome = Biome.objects.filter(country_id=country.id, area__contains=data['location']).first()
        vegetation_area = VegetationArea.objects.filter(country_id=country.id, area__contains=data['location']).first()

        if data.get('municipality_id'):
            try:
                municipality = Municipality.objects.get(id=data['municipality_id'])
            except Municipality.DoesNotExist:
                raise ValidationError({
                    'municipality_id': f'Município não cadastrado.'
                })
            if not state or state.id != municipality.state_id:
                raise ValidationError({
                    'municipality_id': f'Município "{municipality.name} ({municipality.id})" incompatível com as coordenadas passadas em location ou polygon. Certifique-se de utilizar o CRS WGS 84 (SRID 4326).'
                })
        
        data['country_id'] = country.id
        data['state_id'] = state.id if state else None
        data['biome_id'] = biome.id if biome else None
        data['vegetation_type_id'] = vegetation_area.vegetation_type_id if vegetation_area else None

        return data
    
    def create_trait_values(self, site: Site, validated_data):
        trait_values = [
            SiteTraitValue(
                site_id=site.id,
                trait_id=data['trait_id'],
                value=data['value'],
            ) for data in validated_data['trait_values']
        ]

        trait_values = SiteTraitValue.objects.bulk_create(trait_values)

        for trait_value, data in zip(trait_values, validated_data['trait_values']):
            trait = data.pop('trait')
            texts = data.pop('texts')
            value_type = trait.schema['type']
            if value_type == "string" or value_type == "array" and trait.schema['items']['type'] == "string":
                trait_value.texts.add(*texts)

    def update_trait_values(self, site: Site, validated_data):
        with transaction.atomic():
            trait_values_to_delete = []
            trait_values_to_update = []
            trait_values_to_update_data = []
            for trait_value in site.trait_values.all():
                for idx, data in enumerate(validated_data['trait_values']):
                    if trait_value.trait_id == data['trait_id']:
                        if trait_value.value != data['value']:
                            trait_value.value = data['value']
                            trait_value.updated_at = Now()

                        trait_values_to_update.append(trait_value)
                        trait_values_to_update_data.append(validated_data['trait_values'].pop(idx))
                        # pre-existing trait values passed are poped into a new list to be updated
                        break
                else:
                    trait_value.deleted_at = Now() # pre-existing trait values absent from data must be marked as deleted
                    trait_values_to_delete.append(trait_value)

            self.create_trait_values(site, validated_data) # any remaining data refers to new trait values which must be created
            
            SiteTraitValue.objects.bulk_update(trait_values_to_update, ["value", "updated_at"]) # pre-existing values passed are updated
            SiteTraitValue.objects.bulk_update(trait_values_to_delete, ["deleted_at"]) # pre-existing values absent are marked as deleted

            for trait_value, data in zip(trait_values_to_update, trait_values_to_update_data):
                trait = data.pop('trait')
                texts = data.pop('texts')
                value_type = trait.schema['type']
                if value_type == "string" or value_type == "array" and trait.schema['items']['type'] == "string":
                    trait_value.texts.set(texts)

    def create(self, validated_data):
        with transaction.atomic():
            site = Site.objects.create(
                type = self.site_type,
                location = validated_data['location'],
                polygon = validated_data.get('polygon'),
                country_id = validated_data['country_id'],
                state_id = validated_data['state_id'],
                municipality_id = validated_data.get('municipality_id'),
                biome_id = validated_data['biome_id'],
                vegetation_type_id = validated_data['vegetation_type_id'],
            )

            if validated_data.get('trait_values'):
                validated_data['trait_values'] = [ # after data validation, trait and texts can be appended to assist objects creation
                    dict(**data, **{
                        'trait': trait,
                        'texts': texts,
                    }) for trait, texts, data in zip(self.traits, self.trait_values_texts, validated_data.get('trait_values'))
                ]
                self.create_trait_values(site, validated_data)

            return site

    def update(self, site, validated_data):
        with transaction.atomic():
            site.location = validated_data['location']
            site.polygon = validated_data.get('polygon')
            site.country_id = validated_data['country_id']
            site.state_id = validated_data['state_id']
            site.municipality_id = validated_data.get('municipality_id')
            site.biome_id = validated_data['biome_id']
            site.vegetation_type_id = validated_data['vegetation_type_id']
            site.updated_at = Now()
            site.save()

            if validated_data.get('trait_values'):
                validated_data['trait_values'] = [ # after data validation, trait and texts can be appended to assist objects updating
                    dict(**data, **{
                        'trait': trait,
                        'texts': texts,
                    }) for trait, texts, data in zip(self.traits, self.trait_values_texts, validated_data.get('trait_values'))
                ]
                self.update_trait_values(site, validated_data)

            return site
    
    class Meta:
        model = Site
        fields = [
            'location',
            'polygon',
            'area_m2',
            'country',
            'state',
            'municipality',
            'biome',
            'vegetation_type',
            'trait_values',
            'created_at',
            'municipality_id',
        ]

class FarmSerializer(SiteSerializer):
    # read
    site_id = IntegerField(read_only=True)
    user = UserPreviewSerializer(read_only=True)
    # write
    user_id = IntegerField(write_only=True)

    def __init__(self,  *args, **kwargs):
        kwargs['site_type'] = "farm"

        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        data['name'] = none_if_empty(data['name'])

        return super().to_internal_value(data)

    def validate(self, data):
        instance_id = self.instance.id if self.instance else 0

        homonym_farm = Farm.objects.active().filter(
            ~Q(id=instance_id),
            user_id=data['user_id'],
            name=data['name'],
        ).first()
        if homonym_farm:
            raise ValidationError({'name': f'O nome "{data["name"]}" já está sendo utilizado para outra propriedade.'})
        
        return super().validate(data)

    def create(self, validated_data):
        with transaction.atomic():
            site = super().create(validated_data)
            
            return Farm.objects.create(
                site_id = site.id,
                name = validated_data['name'],
                user_id = validated_data['user_id'],
            )

    def update(self, farm, validated_data):
        with transaction.atomic():
            super().update(farm.site, validated_data)

            farm.name = validated_data['name']
            farm.user_id = validated_data['user_id']
            farm.save()
            
            return farm

    class Meta:
        model = Farm
        fields = [
            'id',
            'site_id',
            'name',
            'user_id',
            'user',
        ] + SiteSerializer.Meta.fields

class CroppingPatternCropSerializer(ModelSerializer):
    # read
    plant = PlantPreviewSerializer(read_only=True)
    # write
    plant_id = IntegerField(write_only=True)
    # both
    distance_to_next_crop_m = DecimalField(max_digits=5, decimal_places=2, coerce_to_string=False)

    def validate(self, data):
        if data['distance_to_next_crop_m'] <= 0:
            raise ValidationError({'distance_to_next_crop_m': 'Todo espaçamento entre plantas na mesma linha deve ser maior do que 0.'})
        
        return data

    class Meta:
        model = CroppingPatternCrop
        fields = [
            'position',
            'plant',
            'plant_id',
            'distance_to_next_crop_m',
        ]
    
class CroppingPatternRowSerializer(ModelSerializer):
    # read
    purpose = CharField(read_only=True, source='purpose.text.pt_br')
    # write
    purpose_id = IntegerField(write_only=True, required=False)
    # both
    distance_to_next_row_m = DecimalField(max_digits=5, decimal_places=2, coerce_to_string=False)
    crops_offset_m = DecimalField(max_digits=5, decimal_places=2, coerce_to_string=False)
    crops = CroppingPatternCropSerializer(many=True, source='row_crops')

    def validate(self, data):
        if data['distance_to_next_row_m'] <= 0:
            raise ValidationError({'distance_to_next_row_m': 'Todo espaçamento entre linhas deve ser maior do que 0.'})
        
        return data
        
    @staticmethod
    def create(pattern_id, row_data, row_position):
        pattern_row = CroppingPatternRow.objects.create(
            **dict(
                position = row_position,
                pattern_id = pattern_id,
                purpose_id = row_data.get('purpose_id'),
                crops_offset_m = row_data['crops_offset_m'],
                distance_to_next_row_m = row_data['distance_to_next_row_m'],
            )
        )

        crops = [
            CroppingPatternCrop(
                **dict(
                    **crop,
                    position = j+1,
                    pattern_id = pattern_id,
                    pattern_row_id = pattern_row.id,
                )
            ) for j, crop in enumerate(row_data['row_crops'])
        ]
        CroppingPatternCrop.objects.bulk_create(crops)

    class Meta:
        model = CroppingPatternRow
        fields = [
            'position',
            'purpose',
            'purpose_id',
            'distance_to_next_row_m',
            'crops_offset_m',
            'crops',
        ]

class CroppingPatternParamsSerializer(Serializer):
    with_rows = BooleanField(required=False, allow_null=False, default=True)
    pattern_is_public = BooleanField(required=False, allow_null=False, source='is_public')
    pattern_author_id = IntegerField(required=False, allow_null=False, source='author_id')

class CroppingPatternSerializer(ModelSerializer):
    # read
    author = UserPreviewSerializer(read_only=True)
    # write
    rows = CroppingPatternRowSerializer(write_only=True, many=True, source='pattern_rows')
    author_id = IntegerField(write_only=True)
    # both
    is_public = BooleanField(required=False)

    def __init__(self,  *args, **kwargs):
        params = kwargs.pop('params', {})
        if params.get('with_rows'):
            self.fields['rows'] = CroppingPatternRowSerializer(many=True, source='pattern_rows')

        super().__init__(*args, **kwargs)

    def publish(self, validated_data):
        content = Content.objects.create(
            status = 'accepted',
            type = 'cropping_pattern',
            proposer_id = validated_data.get('author_id'),
            acceptor_id = validated_data.get('author_id'),
            proposed_at = Now(),
            accepted_at = Now(),
        )

        return content

    def retract(self, pattern, validated_data):
        pattern.public_content.update(
            rejector_id = validated_data['author_id'],
            rejected_at = Now(),
        )

    def validate(self, data):
        import pdb; pdb.set_trace()
        self.rows_hash = hash_object(data['pattern_rows'])
        instance_id = self.instance.id if self.instance else 0

        if instance_id:
            pattern = CroppingPattern.objects.get(id=instance_id)
            pattern_dependent_fields = pattern.pattern_fields.filter(~Q(user_id=data['author_id']))
            if pattern_dependent_fields.count() > 0:
                raise ValidationError({
                    'non_field_errors': (
                        'O padrão não pode ser alterado enquanto está sendo utilizado por outros usuários. '
                        'Tente copiar as mudanças que deseja para um novo padrão.'
                    )
                })
            
        homonym_pattern = CroppingPattern.objects.active().filter(
            ~Q(id=instance_id),
            author_id=data['author_id'],
            name=data['name'],
        )
        if homonym_pattern:
            raise ValidationError({
                'name': f'O nome {data["name"]} já está sendo usado para outro padrão criado por você.'
            })

        twin_public_pattern = CroppingPattern.objects.active().public().filter(
            ~Q(id=instance_id),
            rows_hash=self.rows_hash,
            public_content__status='accepted',
        ).first()
        if twin_public_pattern:
            raise ValidationError({
                'rows': (
                    'Uma configuração idêntica já consta em outro padrão publicado: ' 
                    f'"{twin_public_pattern.name}", por {full_name(twin_public_pattern.author)}.'
                )
            })

        return data

    def create(self, validated_data):
        with transaction.atomic():
            content_id = None
            is_public = validated_data.get('is_public', True)
            if is_public:
                content = self.publish(validated_data)
                content_id = content.id

            pattern = CroppingPattern.objects.create(
                name = validated_data['name'],
                description = validated_data['description'],
                author_id = validated_data['author_id'],
                source_pattern_id = validated_data.get('source_pattern_id'),
                rows_hash = self.rows_hash,
                is_public = is_public,
                public_content_id = content_id,
            )

            for i, row_data in enumerate(validated_data['pattern_rows']):
                CroppingPatternRowSerializer.create(pattern.id, row_data, i+1)

            return pattern

    def update(self, pattern, validated_data):
        with transaction.atomic():
            content_id = pattern.public_content_id

            is_public = validated_data.get('is_public', True)
            if is_public and not pattern.is_public:
                content = self.publish(validated_data)
                content_id = content.id
            elif not is_public and pattern.is_public:
                self.retract(pattern, validated_data)

            if pattern.rows_hash != self.rows_hash:
                pattern.pattern_crops.all().delete()
                pattern.pattern_rows.all().delete()

                for i, row_data in enumerate(validated_data['pattern_rows']):
                    CroppingPatternRowSerializer.create(pattern.id, row_data, i+1)

            pattern.name = validated_data['name']
            pattern.description = validated_data['description']
            pattern.author_id = validated_data['author_id']
            pattern.rows_hash = self.rows_hash
            pattern.is_public = is_public
            pattern.public_content_id = content_id
            pattern.updated_at = Now()
            pattern.save()

            return pattern

    class Meta:
        model = CroppingPattern
        fields = [
            'id',
            'name',
            'description',
            'is_public',
            'source_pattern_id',
            'author',
            'author_id',
            'rows',
        ]

class CroppingSerializer(ModelSerializer):
    # both
    pattern_id = IntegerField()
    rows_offset_m = DecimalField(max_digits=6, decimal_places=2)
    crops_offset_m = DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        model = Cropping
        fields = [
            'pattern_id',
            'rows_angle_deg',
            'rows_offset_m',
            'crops_offset_m',
            # 'summary',
            # 'geometry',
            # 'rule_set',
        ]

class FieldSerializer(SiteSerializer):
    # read
    site_id = IntegerField(read_only=True)
    user = UserPreviewSerializer(read_only=True)
    # write
    user_id = IntegerField(write_only=True)
    # both
    farm_id = IntegerField()
    cropping = CroppingSerializer(required=False, allow_null=True)

    def __init__(self,  *args, **kwargs):
        kwargs['site_type'] = "field"

        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        data['name'] = none_if_empty(data['name'])

        return super().to_internal_value(data)

    def validate(self, data):
        instance_id = self.instance.id if self.instance else 0

        homonym_field = Field.objects.active().filter(
            ~Q(id=instance_id),
            farm_id=data['farm_id'],
            name=data['name'],
        ).first()

        if homonym_field:
            raise ValidationError({'name': f'O nome "{data["name"]}" já está sendo utilizado para outra área na mesma propriedade.'})

        if not data.get('polygon'):
            raise ValidationError({'polygon': 'Campo obrigatório.'})
        
        return super().validate(data)

    def create(self, validated_data):
        with transaction.atomic():
            site = super().create(validated_data)

            cropping = Cropping.objects.create(
                pattern_id = validated_data['cropping']['pattern_id'],
                rows_angle_deg = validated_data['cropping']['rows_angle_deg'],
                rows_offset_m = validated_data['cropping']['rows_offset_m'],
                crops_offset_m = validated_data['cropping']['crops_offset_m'],
            ) if validated_data.get('cropping') else None
            
            return Field.objects.create(
                site_id = site.id,
                name = validated_data['name'],
                farm_id = validated_data['farm_id'],
                user_id = validated_data['user_id'],
                cropping = cropping
            )

    def update(self, field, validated_data):
        with transaction.atomic():
            super().update(field.site, validated_data)

            if field.cropping:
                if validated_data.get('cropping'):
                    field.cropping.pattern_id = validated_data['cropping']['pattern_id']
                    field.cropping.rows_angle_deg = validated_data['cropping']['rows_angle_deg']
                    field.cropping.rows_offset_m = validated_data['cropping']['rows_offset_m']
                    field.cropping.crops_offset_m = validated_data['cropping']['crops_offset_m']
                    field.cropping.save()
                else:
                    field.cropping.delete()
            elif validated_data.get('cropping'):
                field.cropping = Cropping.objects.create(
                    pattern_id = validated_data['cropping']['pattern_id'],
                    rows_angle_deg = validated_data['cropping']['rows_angle_deg'],
                    rows_offset_m = validated_data['cropping']['rows_offset_m'],
                    crops_offset_m = validated_data['cropping']['crops_offset_m'],
                )

            field.name = validated_data['name']
            field.farm_id = validated_data['farm_id']
            field.updated_at = Now()
            field.save()
            
            return field

    class Meta:
        model = Field
        fields = [
            'id',
            'site_id',
            'farm_id',
            'name',
            'user_id',
            'user',
            'cropping',
        ] + SiteSerializer.Meta.fields
