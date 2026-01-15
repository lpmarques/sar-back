from django.db.models import IntegerField, Value
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
from geography.models import Biome, ClimateNormal, Country, MonthlyDroughtArea, Municipality, SoilAcidityLevel, SoilPhMap, SoilTextureType, State, VegetationType
from geography.serializers import BiomeParamsSerializer, BiomeSerializer, ClimateNormalParamsSerializer, ClimateNormalSerializer, ClimateNormalsSummary, CountryParamsSerializer, CountrySerializer, DroughtParamsSerializer, DroughtSerializer, DroughtsSummary, ElevationParamsSerializer, ElevationSerializer, MunicipalitySerializer, SoilAcidityLevelSerializer, SoilPhParamsSerializer, SoilPhPixelSerializer, SoilTextureTypeParamsSerializer, SoilTextureTypeSerializer, StateParamsSerializer, StateSerializer, VegetationTypeParamsSerializer, VegetationTypeSerializer

GEOM_FIELDS = ['area']

class CountryView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Country.objects.defer(*GEOM_FIELDS).denormalized()

    def get(self, request, country_id):
        try:
            country = self.get_queryset().get(id=country_id)
        except Country.DoesNotExist:
            content = {'msg': 'País não cadastrado'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = CountrySerializer(country)

        return Response(serializer.data, status=status.HTTP_200_OK)

class CountryListView(CountryView):
    permission_classes = [AllowAny]

    def get(self, request):
        filters = {}
        if request.query_params:
            filters.update(CountryParamsSerializer(request.query_params).data)

        countries = self.get_queryset().filter(**filters)
        serializer = CountrySerializer(countries, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class StateView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return State.objects.defer(*GEOM_FIELDS)

    def get(self, request, state_id):
        try:
            state = State.objects.get_queryset().get(id=state_id)
        except State.DoesNotExist:
            content = {'msg': 'Estado não cadastrado'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = StateSerializer(state)

        return Response(serializer.data, status=status.HTTP_200_OK)

class StateListView(StateView):
    def get(self, request, country_id):
        filters = {}
        if request.query_params:
            filters.update(StateParamsSerializer(request.query_params).data)

        filters.update({'country_id': country_id})

        states = self.get_queryset().filter(**filters).distinct()
        serializer = StateSerializer(states, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class MunicipalityView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Municipality.objects

    def get(self, request, municipality_id):
        try:
            municipality = self.get_queryset().get(id=municipality_id)
        except Municipality.DoesNotExist:
            content = {'msg': 'Estado não cadastrado'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = MunicipalitySerializer(municipality)

        return Response(serializer.data, status=status.HTTP_200_OK)

class MunicipalityListView(MunicipalityView):
    permission_classes = [AllowAny]

    def get(self, request, state_id):
        municipalities = self.get_queryset().filter(state_id=state_id)
        serializer = MunicipalitySerializer(municipalities, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class BiomeView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Biome.objects.defer(*GEOM_FIELDS)

    def get(self, request, biome_id):
        try:
            biome = self.get_queryset().get(id=biome_id)
        except Biome.DoesNotExist:
            content = {'msg': 'Bioma não cadastrado'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = BiomeSerializer(biome)

        return Response(serializer.data, status=status.HTTP_200_OK)

class BiomeListView(BiomeView):
    def get(self, request, country_id):
        filters = {}
        if request.query_params:
            filters.update(BiomeParamsSerializer(request.query_params).data)

        filters.update({'country_id': country_id})

        biomes = self.get_queryset().filter(**filters).distinct()
        serializer = BiomeSerializer(biomes, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class VegetationTypeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, vegetation_type_id):
        try:
            vegetation_type = VegetationType.objects.get(id=vegetation_type_id)
        except VegetationType.DoesNotExist:
            content = {'msg': 'Tipo de vegetação não cadastrada'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = VegetationTypeSerializer(vegetation_type)

        return Response(serializer.data, status=status.HTTP_200_OK)

class VegetationTypeListView(VegetationTypeView):
    def get(self, request, country_id):
        filters = {}
        if request.query_params:
            filters.update(VegetationTypeParamsSerializer(request.query_params).data)

        filters.update({'country_id': country_id})

        vegetation_types = VegetationType.objects.filter(**filters).distinct()
        serializer = VegetationTypeSerializer(vegetation_types, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class LandSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.query_params.get('latlong'):
            content = {'latlong': 'Parâmetro obrigatório.'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        country_filters = CountryParamsSerializer(request.query_params).data
        country = Country.objects.defer(*GEOM_FIELDS).denormalized().filter(
            **country_filters
        ).first()
        
        state_filters = StateParamsSerializer(request.query_params).data
        state = State.objects.defer(*GEOM_FIELDS).filter(
            **dict(state_filters, country_id=country.id)
        ).first()
        
        biome_filters = BiomeParamsSerializer(request.query_params).data
        biome = Biome.objects.defer(*GEOM_FIELDS).filter(
            **dict(biome_filters, country_id=country.id)
        ).first()
        
        vegetation_type_filters = VegetationTypeParamsSerializer(request.query_params).data
        vegetation_type = VegetationType.objects.filter(
            **dict(vegetation_type_filters, vegetation_areas__country_id=country.id)
        ).first()

        summary = {
            'country': CountrySerializer(country).data,
            'state': StateSerializer(state).data,
            'biome': BiomeSerializer(biome).data,
            'vegetation_type': VegetationTypeSerializer(vegetation_type).data,
        }

        return Response(summary, status=status.HTTP_200_OK)


class SoilPhView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.query_params.get('latlong'):
            content = {'latlong': 'Parâmetro obrigatório.'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        filters = SoilPhParamsSerializer(request.query_params).data
        point = filters.get('valued_extent__intersects')

        ph_pixel = SoilPhMap.objects.get_pixel_value(point, filters)
        if not ph_pixel.value:
            content = {'msg': 'Não há estimativa de pH compatível com os parâmetros passados.'}
            return Response(content, status=status.HTTP_404_NOT_FOUND)
            
        serializer = SoilPhPixelSerializer(ph_pixel)

        return Response(serializer.data, status=status.HTTP_200_OK)
 
class SoilAcidityLevelListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        soil_acidity_levels = SoilAcidityLevel.objects.denormalized()
        serializer = SoilAcidityLevelSerializer(soil_acidity_levels, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
  
class SoilTextureTypeListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        filters = {}
        if request.query_params:
            filters.update(SoilTextureTypeParamsSerializer(request.query_params).data)

        soil_texture_types = SoilTextureType.objects.denormalized().filter(**filters)
        serializer = SoilTextureTypeSerializer(soil_texture_types, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class SoilSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.query_params.get('latlong'):
            content = {'latlong': 'Parâmetro obrigatório.'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        ph_filters = SoilPhParamsSerializer(request.query_params).data
        ph_point = ph_filters.get('valued_extent__intersects')
        ph_pixel = SoilPhMap.objects.get_pixel_value(ph_point, ph_filters)
        
        texture_filters = SoilTextureTypeParamsSerializer(request.query_params).data
        texture_type = SoilTextureType.objects.filter(**texture_filters).first()

        summary = {
            'acidity': SoilPhPixelSerializer(ph_pixel if ph_pixel.value else None).data,
            'texture': SoilTextureTypeSerializer(texture_type).data,
        }

        return Response(summary, status=status.HTTP_200_OK)


class ClimateNormalListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        filters = ClimateNormalParamsSerializer(request.query_params).data
        target = filters.pop('target_point', None)

        queryset = ClimateNormal.objects
        
        if target:
            nearest_station = ClimateNormal.objects.get_nearest_station(target, filters)
        
            if not nearest_station:
                content = {'msg': 'Não há normal climatológica compatível com os parâmetros passados.'}
                return Response(content, status=status.HTTP_404_NOT_FOUND)
            
            filters.update({'station_code': nearest_station['station_code']})
            queryset = queryset.annotate(
                station_distance_m=Value(nearest_station['station_distance_m'].m, output_field=IntegerField())
            )

        climate_normals = queryset.filter(**filters)

        serializer = ClimateNormalSerializer(climate_normals, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class DroughtListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        filters = {}
        if request.query_params:
            filters.update(DroughtParamsSerializer(request.query_params).data)

        droughts = MonthlyDroughtArea.objects.defer(*GEOM_FIELDS).filter(**filters).order_by(
            'year',
            'month',
            'drought_level'
        )
        serializer = DroughtSerializer(droughts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class ElevationView(APIView):
    permission_classes = [AllowAny]
    source_url = 'https://api.open-meteo.com/v1/elevation'
    request_timeout_s = 10

    def get(self, request):
        if not request.query_params.get('latlong'):
            content = {'latlong': 'Parâmetro obrigatório.'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        params = ElevationParamsSerializer(request.query_params).data
        point = params.get('latlong')

        try:
            response = requests.get(
                f'{self.source_url}?longitude={point.x}&latitude={point.y}',
                timeout=self.request_timeout_s
            )
            response.raise_for_status()

            serializer = ElevationSerializer(response.json())
        except Exception:
            content = {'msg': 'Erro ao consultar API externa.'}
            return Response(content, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(serializer.data, status=status.HTTP_200_OK)

class ClimateSummaryView(APIView):
    permission_classes = [AllowAny]
    elevation_source_url = 'https://api.open-meteo.com/v1/elevation'
    elevation_request_timeout_s = 10
    
    def get(self, request):
        if not request.query_params.get('latlong'):
            content = {'latlong': 'Parâmetro obrigatório.'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        point = ElevationParamsSerializer(request.query_params).data.get('latlong')
        try:
            response = requests.get(
                f'{self.elevation_source_url}?longitude={point.x}&latitude={point.y}',
                timeout=self.elevation_request_timeout_s
            )
            response.raise_for_status()
            
            elevation = response.json()
        except Exception:
            elevation = None
        
        climate_normals = []
        normals_queryset = ClimateNormal.objects
        normals_filters = ClimateNormalParamsSerializer(request.query_params).data
        normals_target = normals_filters.pop('target_point')
        normals_latest_year = normals_queryset.get_latest_year(normals_filters)
        normals_filters.update(normals_latest_year or {})
        nearest_station = normals_queryset.get_nearest_station(normals_target, normals_filters)
        if nearest_station:
            normals_filters.update({'station_code': nearest_station['station_code']})
            normals_queryset = normals_queryset.annotate(
                station_distance_m=Value(nearest_station['station_distance_m'].m, output_field=IntegerField())
            )

            climate_normals = normals_queryset.filter(**normals_filters)

        droughts_filters = DroughtParamsSerializer(request.query_params).data
        droughts = MonthlyDroughtArea.objects.defer(*GEOM_FIELDS).filter(**droughts_filters)

        summary = {
            'elevation': ElevationSerializer(elevation).data,
            'normals': ClimateNormalsSummary(climate_normals or None).data,
            'droughts': DroughtsSummary(droughts or None).data,
        }

        return Response(summary, status=status.HTTP_200_OK)
