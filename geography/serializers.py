from django.contrib.gis.geos import Point
from rest_framework.serializers import CharField, DecimalField, Field, IntegerField, ModelSerializer, Serializer, SerializerMethodField, SlugRelatedField, ValidationError
from geography.models import Biome, ClimateNormal, Country, MonthlyDroughtArea, Municipality, SoilAcidityLevel, SoilPhMap, SoilTextureType, State, VegetationType
import pandas as pd
import numpy as np
import re

class StringListParamField(Field):
    def __init__(self, separator=",", *args, **kwargs):
        self.separator = separator
        super().__init__(*args, **kwargs)
    
    def to_representation(self, value: str) -> list:
        return value.split(self.separator) if value else None

    def to_internal_value(self, value: list) -> str:
        return self.separator.join(value) if value else None

class PointParamField(Field):
    latlong_pattern = r'^(-?\d{,2}(?:\.\d+)?),(-?\d{,3}(?:\.\d+)?)$'

    def __init__(self, srid=4326, *args, **kwargs):
        self.srid = srid
        super().__init__(*args, **kwargs)

    def to_representation(self, value: str) -> Point:
        latlong_match = re.match(self.latlong_pattern, value)
        if not latlong_match:
            raise ValidationError({'latlong': f"Valor '{value}' inválido. Utilize o formato {self.latlong_pattern}."})

        lat, long = latlong_match.groups()
        lat = float(lat)
        long = float(long)

        if lat > 90 or lat < -90:
            raise ValidationError({'latlong': f"Latitude {lat} inválida. Utilize um valor entre -90° e 90°."})

        if long > 180 or long < -180:
            raise ValidationError({'latlong': f"Longitude {long} inválida. Utilize um valor entre -180° e 180°."})

        return Point(long, lat, srid=self.srid)

    def to_internal_value(self, value: Point) -> str:
        return value.wkt


class CountryParamsSerializer(Serializer):
    area__contains = PointParamField(required=False, source='latlong')

class CountrySerializer(ModelSerializer):
    name = SlugRelatedField(read_only=True, source='name_text', slug_field='pt_br')

    class Meta:
        model = Country
        fields = [
            'id',
            'name',
        ]

class StateParamsSerializer(Serializer):
    area__contains = PointParamField(required=False, source='latlong')
    vegetation_areas__biome_id = IntegerField(required=False, source='biome_id')
    
class StateSerializer(ModelSerializer):
    name = CharField(read_only=True)
    code = CharField(read_only=True)
    country_id = IntegerField(read_only=True)

    class Meta:
        model = State
        fields = [
            'id',
            'name',
            'code',
            'country_id',
        ]

class MunicipalitySerializer(ModelSerializer):
    name = CharField(read_only=True)
    state_id = IntegerField(read_only=True)
    country_id = IntegerField(read_only=True)
    fiscal_module_size_m2 = IntegerField(read_only=True, source='fiscal_module_size_sqrm')

    class Meta:
        model = Municipality
        fields = [
            'id',
            'name',
            'state_id',
            'country_id',
            'fiscal_module_size_m2',
        ]

class BiomeParamsSerializer(Serializer):
    vegetation_areas__state_id = IntegerField(required=False, allow_null=False, source='state_id')
    area__contains = PointParamField(required=False, source='latlong')

class BiomeSerializer(ModelSerializer):
    name = CharField(read_only=True)
    country_id = IntegerField(read_only=True)

    class Meta:
        model = Biome
        fields = [
            'id',
            'name',
            'country_id',
        ]

class VegetationTypeParamsSerializer(Serializer):
    vegetation_areas__area__contains = PointParamField(required=False, source='latlong')
    vegetation_areas__state_id = IntegerField(required=False, allow_null=False, source='state_id')
    vegetation_areas__biome_id = IntegerField(required=False, allow_null=False, source='biome_id')

class VegetationTypeSerializer(ModelSerializer):
    name = CharField(read_only=True)
    country_id = IntegerField(read_only=True)

    class Meta:
        model = VegetationType
        fields = [
            'id',
            'name',
            'country_id',
        ]

class SoilAcidityLevelSerializer(ModelSerializer):
    name = CharField(read_only=True, source='name_text.pt_br')
    ph_min = DecimalField(max_digits=3, decimal_places=1, read_only=True)
    ph_max = DecimalField(max_digits=3, decimal_places=1, read_only=True)

    class Meta:
        model = SoilAcidityLevel
        fields = [
            'id',
            'name',
            'ph_min',
            'ph_max',
        ]

class SoilPhParamsSerializer(Serializer):
    tile_extent__intersects = PointParamField(source='latlong')
    country_id = IntegerField(required=False)
    state_id = IntegerField(required=False)

class SoilPhPixelSerializer(ModelSerializer):
    ph = DecimalField(max_digits=3, decimal_places=1, read_only=True, source='value')
    acidity_level = SerializerMethodField(read_only=True)

    def get_acidity_level(self, obj):
        round_ph = round(obj.value, 1)
        level = SoilAcidityLevel.objects.denormalized().filter(
            ph_min__lte=round_ph,
            ph_max__gte=round_ph
        ).first()

        return SoilAcidityLevelSerializer(level).data

    class Meta:
        model = SoilPhMap
        fields = [
            'ph',
            'acidity_level',
        ]

class SoilTextureTypeParamsSerializer(Serializer):
    soil_texture_areas__area__contains = PointParamField(required=False, source='latlong')

class SoilTextureTypeSerializer(ModelSerializer):
    name = CharField(read_only=True, source='name_text.pt_br')

    class Meta:
        model = SoilTextureType
        fields = [
            'id',
            'name',
        ]
    
class ClimateNormalParamsSerializer(Serializer):
    target_point = PointParamField(required=False, source='latlong')
    country_id = IntegerField(required=False)
    state_id = IntegerField(required=False)
    period_first_year = IntegerField(required=False, source='first_year')
    period_last_year = IntegerField(required=False, source='last_year')
    month__in = StringListParamField(required=False, source='months')

class ClimateNormalSerializer(ModelSerializer):
    station_elevation_m = IntegerField(read_only=True, source='elevation_m')
    station_distance_m = IntegerField(read_only=True)

    class Meta:
        model = ClimateNormal
        fields = [
            'country_id',
            'state_id',
            'station_code',
            'station_elevation_m',
            'station_distance_m',
            'period_first_year',
            'period_last_year',
            'month',
            'precipitation_mm',
            'temperature_c_minimum',
            'temperature_c_average',
            'temperature_c_maximum',
        ]

class ClimateNormalsSummary(Serializer):
    first_year = IntegerField(read_only=True)
    last_year = IntegerField(read_only=True)
    station_code = IntegerField(read_only=True)
    station_elevation_m = IntegerField(read_only=True)
    station_distance_m = IntegerField(read_only=True)
    annual_precipitation_mm = IntegerField(read_only=True)
    temperature_c_minimum = IntegerField(read_only=True)
    temperature_c_maximum = IntegerField(read_only=True)

    def to_representation(self, instance):
        data = pd.DataFrame(instance.values(
            'station_code',
            'elevation_m',
            'station_distance_m',
            'period_first_year',
            'period_last_year',
            'precipitation_mm',
            'temperature_c_minimum',
            'temperature_c_maximum',
        ))

        data = data.groupby([
            'station_code',
            'elevation_m',
            'station_distance_m',
            'period_first_year',
            'period_last_year',
        ]).agg(
            annual_precipitation_mm=('precipitation_mm', 'sum'),
            temperature_c_minimum=('temperature_c_minimum', 'min'),
            temperature_c_maximum=('temperature_c_maximum', 'max'),
        ).reset_index().rename({
            'period_first_year': 'first_year',
            'period_last_year': 'last_year',
            'elevation_m': 'station_elevation_m',
        }, axis=1).replace({
            np.nan: None
        }).to_dict(orient='records')[0]

        return super().to_representation(data)

class DroughtParamsSerializer(Serializer):
    country_id = IntegerField(required=False)
    area__contains = PointParamField(required=False, source='latlong')
    year__in = StringListParamField(required=False, source='years')
    month__in = StringListParamField(required=False, source='months')

class DroughtSerializer(ModelSerializer):
    class Meta:
        model = MonthlyDroughtArea
        fields = [
            'year',
            'month',
            'drought_level',
            'drought_level_code',
            'country_id',
        ]

class DroughtsSummary(Serializer):
    first_year = IntegerField(read_only=True)
    first_month = IntegerField(read_only=True)
    last_year = IntegerField(read_only=True)
    last_month = IntegerField(read_only=True)
    period_months = IntegerField(read_only=True)
    drought_months = IntegerField(read_only=True)
    s0_drought_months = IntegerField(read_only=True)
    s1_drought_months = IntegerField(read_only=True)
    s2_drought_months = IntegerField(read_only=True)
    s3_drought_months = IntegerField(read_only=True)
    s4_drought_months = IntegerField(read_only=True)

    def to_representation(self, instance):
        data = pd.DataFrame(instance.values(
            'country_id',
            'year',
            'month',
            'drought_level',
        ))
        data['year_month'] = pd.to_datetime(data[['year', 'month']].assign(day=1))

        data = data.groupby('country_id').agg(
            first_year=('year', 'min'),
            first_month=('year_month', lambda x: x.min().month),
            last_year=('year', 'max'),
            last_month=('year_month', lambda x: x.max().month),
            period_months=('year_month', lambda x: (x.max().year - x.min().year) * 12 + x.max().month - x.min().month + 1),
            s0_drought_months=('drought_level', lambda x: (x==1).sum()),
            s1_drought_months=('drought_level', lambda x: (x==2).sum()),
            s2_drought_months=('drought_level', lambda x: (x==3).sum()),
            s3_drought_months=('drought_level', lambda x: (x==4).sum()),
            s4_drought_months=('drought_level', lambda x: (x==5).sum()),
        ).reset_index(drop=True).to_dict(orient='records')[0]

        return super().to_representation(data)

class ElevationParamsSerializer(Serializer):
    latlong = PointParamField()

class ElevationSerializer(Serializer):
    elevation_m = IntegerField()

    def to_representation(self, obj):
        if obj.get('error'):
            raise Exception
        
        data = {
            'elevation_m': obj['elevation'][0]
        }
        
        return super().to_representation(data)
