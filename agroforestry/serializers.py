from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Now
from jsonschema import FormatChecker, validate
from rest_framework_gis.fields import GeometryField
from rest_framework.serializers import BooleanField, CharField, DateTimeField, IntegerField, JSONField, ModelSerializer, SerializerMethodField, ValidationError
from core.serializers import UserPreviewSerializer
from core.models import Text
from geography.models import Biome, Country, Municipality, State, VegetationArea
from geography.serializers import BiomeSerializer, CountrySerializer, MunicipalitySerializer, StateSerializer, VegetationTypeSerializer
from agroforestry.models import Farm, Field, Site, SiteTrait, SiteTraitTextValueOption, SiteTraitValue
from agroforestry.utils import none_if_empty
from typing import Union
import json

class SiteSerializer(ModelSerializer):
    # both
    location = GeometryField(required=False, source='site.location')
    polygon = GeometryField(required=False, source='site.polygon')
    # write
    municipality_id = IntegerField(write_only=True, required=False)
    # read
    area_m2 = SerializerMethodField()
    country = CountrySerializer(read_only=True, source='site.country')
    state = StateSerializer(read_only=True, source='site.state')
    municipality = MunicipalitySerializer(read_only=True, source='site.municipality')
    biome = BiomeSerializer(read_only=True, source='site.biome')
    vegetation_type = VegetationTypeSerializer(read_only=True, source='site.vegetation_type')
    created_at = DateTimeField(read_only=True, source='site.created_at')
    
    def __init__(self,  *args, **kwargs):
        self.site_type = kwargs.pop('site_type')

        super().__init__(*args, **kwargs)

    def get_area_m2(self, obj):
        polygon = obj.site.polygon
        if polygon:
            polygon.transform(3857) # using web mercator CRS for area in square meters
            return round(polygon.area)
        
        return None
    
    def georep_to_geos(self, rep: Union[dict, str]):
        if not rep:
            return None
        if isinstance(rep, dict):
            rep = json.dumps(rep)

        return GEOSGeometry(rep)
    
    def to_internal_value(self, data):
        return data # must skip default method to avoid fields nesting on write

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
                'non_field_errors': 'As coordenadas passadas em location ou polygon não correspondem a terra firme. Certifique-se de utilizar o CRS WGS 84 (SRID 4326).'
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

    def create(self, validated_data):
        return Site.objects.create(
            type = self.site_type,
            location = validated_data['location'],
            polygon = validated_data.get('polygon'),
            country_id = validated_data['country_id'],
            state_id = validated_data['state_id'],
            municipality_id = validated_data.get('municipality_id'),
            biome_id = validated_data['biome_id'],
            vegetation_type_id = validated_data['vegetation_type_id'],
        )

    def update(self, site, validated_data):
        site.location = validated_data['location']
        site.polygon = validated_data.get('polygon')
        site.country_id = validated_data['country_id']
        site.state_id = validated_data['state_id']
        site.municipality_id = validated_data.get('municipality_id')
        site.biome_id = validated_data['biome_id']
        site.vegetation_type_id = validated_data['vegetation_type_id']
        site.updated_at = Now()
        site.save()

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
            'created_at',
            'municipality_id',
        ]

class FarmSerializer(SiteSerializer):
    # both
    name = CharField()
    # write
    user_id = IntegerField(write_only=True)
    # read
    site_id = IntegerField(read_only=True)
    user = UserPreviewSerializer(read_only=True)

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

class FieldSerializer(SiteSerializer):
    # both
    name = CharField()
    farm_id = IntegerField()
    # write
    user_id = IntegerField(write_only=True)
    # read
    site_id = IntegerField(read_only=True)
    user = UserPreviewSerializer(read_only=True)

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

        if 'polygon' not in data:
            raise ValidationError({'polygon': 'Campo obrigatório.'})
        
        return super().validate(data)

    def create(self, validated_data):
        with transaction.atomic():
            site = super().create(validated_data)
            
            return Field.objects.create(
                site_id = site.id,
                name = validated_data['name'],
                farm_id = validated_data['farm_id'],
                user_id = validated_data['user_id'],
            )

    def update(self, field, validated_data):
        with transaction.atomic():
            super().update(field.site, validated_data)

            field.name = validated_data['name']
            field.farm_id = validated_data['farm_id']
            field.user_id = validated_data['user_id']
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
            # 'cropping_summary',
            # 'cropping_geometry',
            # 'cropping_pattern',
            # 'cropping_rule_set',
        ] + SiteSerializer.Meta.fields

class SiteTraitTextValueOptionSerializer(ModelSerializer):
    value = CharField(read_only=True, source='value_text.pt_br')
    description = CharField(read_only=True, source='description_text.pt_br')

    class Meta:
        model = SiteTraitTextValueOption
        fields = [
            'value',
            'description',
        ]
        
class SiteTraitSerializer(ModelSerializer):
    name = CharField(read_only=True, source='name_text.pt_br')
    section = CharField(read_only=True, source='section_text.pt_br')
    schema = JSONField(read_only=True)
    is_nullable = BooleanField(read_only=True)
    text_value_options = SiteTraitTextValueOptionSerializer(read_only=True, many=True, source='site_trait_text_value_options')

    class Meta:
        model = SiteTrait
        fields = [
            'id',
            'name',
            'section',
            'schema',
            'is_nullable',
            'text_value_options',
        ]

class SiteTraitValueSerializer(ModelSerializer):
    # both
    value = CharField()
    site_id = IntegerField()
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
    
    def to_internal_value(self, data):
        value = data.get('value')
        if value is None:
            raise ValidationError({'value': "Campo obrigatório."})

        try:
            trait = SiteTrait.objects.denormalized().get(id=data.get('trait_id'))
        except SiteTrait.DoesNotExist:
            raise ValidationError({'trait_id': "Não há traço cadastrado com esse id."})

        if trait.schema['type'] == "array" and trait.schema['items']['type'] == "string":
            self.texts = Text.objects.filter(**{'pt_br__in': value})
            data['value'] = json.dumps(sorted([text.en for text in self.texts]))
        elif trait.schema['type'] == "string":
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
            raise ValidationError({'non_field_value': f"Já existe um valor do traço '{trait.name_text.pt_br}' (trait_id: {trait.id}) para esse local (site_id: {self.site.id})."})

        try:
            validate(value, trait.schema, format_checker=FormatChecker())
        except Exception as e:
            raise ValidationError({'value': f"Valor inválido para o traço '{trait.name_text.pt_br}' (trait_id: {trait.id}): {e}"})
        
        return data

    def create(self, validated_data):
        with transaction.atomic():
            trait_value = SiteTraitValue.objects.create(
                site_id = validated_data['site_id'],
                trait_id = validated_data['trait_id'],
                value = validated_data['value'],
            )

            value_type = self.trait.schema['type']
            if value_type == "string" or value_type == "array" and self.trait.schema['items']['type'] == "string":
                trait_value.texts.add(*self.texts)

            return trait_value

    def update(self, trait_value, validated_data):
        with transaction.atomic():
            value_type = self.trait.schema['type']
            if trait_value.value != validated_data['value'] and (
                value_type == "string" or value_type == "array" and self.trait.schema['items']['type'] == "string"
            ):
                trait_value.texts.clear()
                trait_value.texts.add(*self.texts)

            trait_value.site_id = validated_data['site_id']
            trait_value.trait_id = validated_data['trait_id']
            trait_value.value = validated_data['value']
            trait_value.save()

            return trait_value

    class Meta:
        model = SiteTraitValue
        fields = [
            'id',
            'site_id',
            'trait_id',
            'trait_slug',
            'trait_name',
            'section_slug',
            'section_name',
            'schema',
            'value',
        ]
