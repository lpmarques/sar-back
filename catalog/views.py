from django.contrib.postgres.aggregates import ArrayAgg
import pandas as pd
import json
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from catalog.models import Plant, PlantNaturalOccurrenceRegion, PlantPopularName, PlantScientificName, PlantValue
from catalog.serializers.models import *
from catalog.serializers.parameters import *
from catalog.serializers.values import *
from core.models import ContentEndorsement
from core.serializers import ContentEndorsementSerializer

class PlantView(APIView):
    permission_classes = [AllowAny]

    def fetch_filter_params(self, params_data: dict, relation_name: str):
        return { key.replace(f'{relation_name}_', ''): value for key, value in params_data.items() if f'{relation_name}_' in key }

    def get_queryset(self):
        params = PlantParamsSerializer(self.request.query_params).data

        query = Plant.objects.with_popular_names(PopularNameFilterParamsSerializer(self.fetch_filter_params(params, 'popular_names')).data) if params.get('with_popular_names') else Plant.objects
        query = query.with_scientific_names(ScientificNameFilterParamsSerializer(self.fetch_filter_params(params, 'scientific_names')).data) if params.get('with_scientific_names') else query
        query = query.with_trait_values(PlantTraitValueFilterParamsSerializer(self.fetch_filter_params(params, 'trait_values')).data) if params.get('with_trait_values') else query
        query = query.with_natural_occurrence_regions(NaturalOccurrenceRegionParamsSerializer(self.fetch_filter_params(params, 'natural_occurrence_regions')).data) if params.get('with_natural_occurrence_regions') else query

        return query

    def get(self, request, plant_id):
        params = PlantParamsSerializer(request.query_params)

        try:
            plant = self.get_queryset().get(id=plant_id)
        except Plant.DoesNotExist:
            content = {'msg': 'Planta não cadastrada'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = PlantSerializer(plant, params=params.data)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PlantListView(PlantView):
    permission_classes = [AllowAny]

    def get(self, request):
        filters = PlantParamsSerializer(self.fetch_filter_params(request.query_params, 'plant')).data
        plants = self.get_queryset().filter(**filters)

        serializer = PlantSerializer(plants, many=True, params=PlantParamsSerializer(request.query_params).data)

        return Response(serializer.data, status=status.HTTP_200_OK)


class TraitListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        filters = {'is_site_specific': False}
        filters.update(TraitFilterParamsSerializer(request.query_params).data)

        traits = PlantTrait.objects.denormalized().filter(**filters)

        serializer = TraitSerializer(traits, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PlantTraitValueListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, plant_id):
        filters = PlantTraitValueFilterParamsSerializer(request.query_params).data
        filters.update({'plant_id': plant_id})

        try:
            plant = Plant.objects.get(id=plant_id)
            trait_values = PlantValue.objects.denormalized().filter(**filters)
        except Plant.DoesNotExist:
            content = {'msg': 'Planta não cadastrada'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = PlantTraitValueSerializer(trait_values, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PopularNameListView(APIView):
    permission_classes = [AllowAny]

    def group_by_popular_name(self, data):
        grouped_df = pd.DataFrame(data).groupby(['name', 'content_status']).agg(plant_ids=('plant_id', lambda x: list(x)))
        
        return grouped_df.reset_index().to_dict(orient='records')
    
    def get_queryset(self):
        filters = PopularNameFilterParamsSerializer(self.request.query_params).data

        return PlantPopularName.objects.filter(**filters)

    def get(self, request):
        popular_names = self.get_queryset()
        serializer = PopularNameSerializer(popular_names, many=True)
        data = self.group_by_popular_name(serializer.data) # TODO: convert this step into values aggregation + value queryset serialization

        return Response(data, status=status.HTTP_200_OK)
    

class PlantPopularNameListView(PopularNameListView):
    def get(self, request, plant_id):
        try:
            plant = Plant.objects.get(id=plant_id)
            popular_names = self.get_queryset().denormalized().filter(plant_id=plant_id)
        except Plant.DoesNotExist:
            content = {'msg': 'Planta não cadastrada'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = PlantPopularNameSerializer(popular_names, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ScientificNameListView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        filters = ScientificNameFilterParamsSerializer(self.request.query_params).data

        return PlantScientificName.objects.filter(**filters)

    def get(self, request):
        scientific_names = self.get_queryset()
        serializer = ScientificNameSerializer(scientific_names, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PlantScientificNameListView(ScientificNameListView):
    def get(self, request, plant_id):
        try:
            plant = Plant.objects.get(id=plant_id)
            scientific_names = self.get_queryset().denormalized().filter(plant_id=plant_id)
        except Plant.DoesNotExist:
            content = {'msg': 'Planta não cadastrada'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PlantScientificNameSerializer(scientific_names, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class NaturalOccurrenceRegionListView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        filters = NaturalOccurrenceRegionParamsSerializer(self.request.query_params).data
        return PlantNaturalOccurrenceRegion.objects.denormalized().filter(**filters)
        
    def get(self, request):
        natural_occurrence_regions = self.get_queryset().values(
            'country__name_text__pt_br',
            'state__code',
            'biome__name',
            'vegetation_type__name'
        ).annotate(plant_ids=ArrayAgg("plant_id"))
        serializer = NaturalOccurrenceRegionSerializer(natural_occurrence_regions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PlantNaturalOccurrenceRegionListView(NaturalOccurrenceRegionListView):
    def get(self, request, plant_id):
        try:
            plant = Plant.objects.get(id=plant_id)
            natural_occurrence_regions = self.get_queryset().filter(plant_id=plant_id)
        except Plant.DoesNotExist:
            content = {'msg': 'Planta não cadastrada'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = PlantNaturalOccurrenceRegionSerializer(natural_occurrence_regions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
