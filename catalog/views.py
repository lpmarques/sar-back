import pandas as pd
from django.db.models import Prefetch
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from catalog.models import Plant, PlantPopularName, PlantScientificName, PlantValue
from catalog.serializers import *

class PlantView(APIView):
    permission_classes = [AllowAny]
    
    param_to_filter_keys = {
        'plant_status': 'content_status',
        'popular_names_status': 'content_status',
        'scientific_names_status': 'content_status',
        'scientific_names_taxonomic_status': 'taxonomic_status',
        'trait_values_status': 'content_status',
        'trait_values_trait_keys': 'trait__name__in',
        'trait_values_section_keys': 'trait__section__in'
    }

    def fetch_filters(self, params_data: dict, relation_name: str):
        return { self.param_to_filter_keys.get(key): value for key, value in params_data.items() if key in params_data.keys() and f'{relation_name}_' in key }

    def get_queryset(self):
        params = PlantParamsSerializer(self.request.query_params)

        query = Plant.objects.with_popular_names(self.fetch_filters(params.data, 'popular_names')) if params.data.get('with_popular_names') else Plant.objects
        query = query.with_scientific_names(self.fetch_filters(params.data, 'scientific_names')) if params.data.get('with_scientific_names') else query
        query = query.with_trait_values(self.fetch_filters(params.data, 'trait_values')) if params.data.get('with_trait_values') else query

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
        params = PlantParamsSerializer(request.query_params)
        filters = {'content_status': 'accepted'}
        filters.update(self.fetch_filters(params.data, 'plant'))

        plants = self.get_queryset().filter(**filters)

        serializer = PlantSerializer(plants, many=True, params=params.data)

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
        extra_filters = PlantTraitValueFilterParamsSerializer(request.query_params).data

        try:
            plant = Plant.objects.get(id=plant_id, content_status='accepted')
            trait_values = PlantValue.objects.denormalized().filter(plant_id=plant_id, content_status='accepted', **extra_filters)
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
    
    def get_queryset(self):
        filters = {'content_status': 'accepted'}
        filters.update(PopularNameFilterParamsSerializer(self.request.query_params).data)

        return PlantPopularName.objects.filter(**filters)

    def get(self):
        popular_names = self.get_queryset()
        serializer = PopularNameSerializer(popular_names, many=True)
        data = self.group_by_popular_name(serializer.data) # TODO: consider changing relation to M2M and removing this step

        return Response(data, status=status.HTTP_200_OK)
    

class PlantPopularNameListView(PopularNameListView):
    def get(self, request, plant_id):
        popular_names = self.get_queryset().filter(plant_id=plant_id)
        serializer = PlantPopularNameSerializer(popular_names, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ScientificNameListView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        filters = {'content_status': 'accepted'}
        filters.update(ScientificNameFilterParamsSerializer(self.request.query_params).data)

        return PlantScientificName.objects.filter(**filters)

    def get(self):
        scientific_names = self.get_queryset()
        serializer = ScientificNameSerializer(scientific_names, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PlantScientificNameListView(ScientificNameListView):

    def get(self, request, plant_id):
        scientific_names = self.get_queryset().filter(plant_id=plant_id)
        serializer = PlantScientificNameSerializer(scientific_names, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
