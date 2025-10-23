from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from geography.models import Biome, Country, Municipality, State, VegetationType
from geography.serializers import BiomeParamsSerializer, BiomeSerializer, CountrySerializer, StateParamsSerializer, StateSerializer, MunicipalitySerializer, VegetationTypeParamsSerializer, VegetationTypeSerializer

GEOM_FIELDS = ['area']

class CountryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        countries = Country.objects.defer(*GEOM_FIELDS).select_related('name_text').all()
        serializer = CountrySerializer(countries, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class CountryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, country_id):
        try:
            country = Country.objects.defer(*GEOM_FIELDS).get(id=country_id)
        except Country.DoesNotExist:
            content = {'msg': 'País não cadastrado'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = CountrySerializer(country)

        return Response(serializer.data, status=status.HTTP_200_OK)

class StateView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return State.objects.defer(*GEOM_FIELDS)

    def get(self, request, state_id):
        try:
            state = State.objects.defer(*GEOM_FIELDS).get(id=state_id)
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


class MunicipalityListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, state_id):
        municipalities = Municipality.objects.filter(state_id=state_id)
        serializer = MunicipalitySerializer(municipalities, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class MunicipalityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, municipality_id):
        try:
            municipality = Municipality.objects.defer(*GEOM_FIELDS).get(id=municipality_id)
        except Municipality.DoesNotExist:
            content = {'msg': 'Estado não cadastrado'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = MunicipalitySerializer(municipality)

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
