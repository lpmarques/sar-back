from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from geography.models import Country, Municipality, State
from geography.serializers import CountrySerializer, StateSerializer, MunicipalitySerializer

GEOM_DEFERED_FIELDS = ['area','created_at','updated_at']

class CountryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        countries = Country.objects.defer(*GEOM_DEFERED_FIELDS).select_related('name_text').all()
        serializer = CountrySerializer(countries, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class CountryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, country_id):
        try:
            country = Country.objects.defer(*GEOM_DEFERED_FIELDS).get(id=country_id)
        except Country.DoesNotExist:
            content = {'msg': 'País não cadastrado'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = CountrySerializer(country)

        return Response(serializer.data, status=status.HTTP_200_OK)


class StateListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, country_id):
        states = State.objects.defer(*GEOM_DEFERED_FIELDS).prefetch_related('country').filter(country_id=country_id)
        serializer = StateSerializer(states, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class StateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, state_id):
        try:
            state = State.objects.defer(*GEOM_DEFERED_FIELDS).get(id=state_id)
        except State.DoesNotExist:
            content = {'msg': 'Estado não cadastrado'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = StateSerializer(state)

        return Response(serializer.data, status=status.HTTP_200_OK)


class MunicipalityListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, state_id):
        municipalities = Municipality.objects.defer(*GEOM_DEFERED_FIELDS).prefetch_related('state').filter(state_id=state_id)
        serializer = MunicipalitySerializer(municipalities, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class MunicipalityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, municipality_id):
        try:
            municipality = Municipality.objects.defer(*GEOM_DEFERED_FIELDS).get(id=municipality_id)
        except Municipality.DoesNotExist:
            content = {'msg': 'Estado não cadastrado'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = MunicipalitySerializer(municipality)

        return Response(serializer.data, status=status.HTTP_200_OK)
