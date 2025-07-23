import json
import pandas as pd
from django.db.models import Prefetch
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from catalog.models import Plant, PlantPopularName, PlantScientificName, PlantValue
from catalog.serializers import PlantSerializer, PlantQueryParamsSerializer, PlantTraitValueSerializer, PopularNameSerializer, ScientificNameSerializer


class PlantView(APIView):
    permission_classes = [AllowAny]

    def get_prefetches(
            self,
            scientific_names: bool = False,
            scientific_names_status: str = "accepted",
            scientific_names_taxonomic_status: str = None,
            popular_names: bool = False,
            popular_names_status: str = "accepted",
            trait_values: bool = False,
            trait_values_status: str = "accepted",
            trait_values_trait_keys: str = None,
            trait_values_section_key: str = None,
            *args
        ):
        prefetches = []
        if scientific_names:
            filters = {}
            filters.update({'content_status': scientific_names_status} if scientific_names_status else {})
            filters.update({'taxonomic_status': scientific_names_taxonomic_status} if scientific_names_taxonomic_status else {})
            prefetches.append(
                Prefetch(
                    'scientific_names',
                    queryset=PlantScientificName.objects.filter(**filters)
                ),
            )
        if popular_names:
            filters = {}
            filters.update({'content_status': popular_names_status} if popular_names_status else {})
            prefetches.append(
                Prefetch(
                    'popular_names',
                    queryset=PlantPopularName.objects.filter(**filters)
                )
            )
        if trait_values:
            filters = {}
            filters.update({'content_status': trait_values_status} if trait_values_status else {})
            filters.update({'trait__name__in': trait_values_trait_keys} if trait_values_trait_keys else {})
            filters.update({'trait__section': trait_values_section_key} if trait_values_section_key else {})
            prefetches.append(
                Prefetch(
                    'values',
                    queryset=PlantValue.objects.denormalized().filter(**filters)
                )
            )

        return prefetches

    def get(self, request, plant_id):
        serializer = PlantQueryParamsSerializer(request.query_params)
        prefetches = self.get_prefetches(**serializer.data)

        try:
            queryset = Plant.objects
            if prefetches:
                queryset = queryset.prefetch_related(*prefetches)
            plant = queryset.get(id=plant_id)

        except Plant.DoesNotExist:
            content = {'msg': 'Planta não cadastrada'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = PlantSerializer(plant, params=request.query_params.dict())

        return Response(serializer.data, status=status.HTTP_200_OK)

class PlantListView(PlantView):

    def get(self, request):
        serializer = PlantQueryParamsSerializer(request.query_params)
        prefetches = self.get_prefetches(**serializer.data)

        queryset = Plant.objects
        if prefetches:
            queryset = queryset.prefetch_related(*prefetches)
        plants = queryset.filter(content_status="accepted")

        serializer = PlantSerializer(plants, many=True, params=request.query_params.dict())

        return Response(serializer.data, status=status.HTTP_200_OK)
  
class PlantTraitListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, plant_id):
        try:
            plant = Plant.objects.get(id=plant_id, content_status='accepted')
            trait_values = PlantValue.objects.denormalized().filter(plant_id=plant.id, content_status='accepted')
        except Plant.DoesNotExist:
            content = {'msg': 'Planta não cadastrada'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        except PlantValue.DoesNotExist:
            content = {'msg': 'Nenhum traço encontrado para a planta'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = PlantTraitValueSerializer(trait_values, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class PopularNameListView(APIView):
    permission_classes = [AllowAny]

    def group_by_popular_name(self, data): # TODO: convert this to serializer method to_representation
        grouped_df = pd.DataFrame(data).groupby('name').agg(plant_ids=('plant_id', lambda x: list(x)))
        
        return grouped_df.reset_index().to_dict(orient='records')

    def get(self, request, plant_id=None):
        optional_filters = {'plant_id': plant_id} if plant_id else {}
        popular_names = PlantPopularName.objects.filter(content_status='accepted', **optional_filters)
        serializer = PopularNameSerializer(popular_names, many=True)
        
        data = self.group_by_popular_name(serializer.data) # TODO: consider changing relation to M2M and removing this step
        return Response(data, status=status.HTTP_200_OK)

class ScientificNameListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, plant_id=None):
        optional_filters = {'plant_id': plant_id} if plant_id else {}
        scientific_names = PlantScientificName.objects.filter(content_status='accepted', **optional_filters).prefetch_related(
            Prefetch('plant', queryset=Plant.objects.filter(content_status='accepted')))
        serializer = ScientificNameSerializer(scientific_names, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
