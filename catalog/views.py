# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

from abc import ABC
from django.contrib.postgres.aggregates import ArrayAgg
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from catalog.services import get_plant
from core.views import ContentListView, ContentView, ContentView
from catalog.models import Plant, NaturalOccurrenceRegion, PopularName, Taxon, TraitValue
from catalog.serializers.models import *
from catalog.serializers.parameters import *

class PlantView(ContentView):
    model_class = Plant
    serializer_class = PlantSerializer

    def fetch_filter_params(self, params_data: dict, related_name: str):
        return { key.replace(f'{related_name}_', ''): value for key, value in params_data.items() if f'{related_name}_' in key }

    def get_queryset(self):
        params = PlantParamsSerializer(self.request.query_params).data

        query = Plant.objects.denormalized().filter(**self.fetch_filter_params(params, 'plant'))
        query = query.with_popular_names(PopularNameParamsSerializer(self.fetch_filter_params(params, 'popular_names')).data) if params.get('with_popular_names') else query
        query = query.with_taxa(TaxonParamsSerializer(self.fetch_filter_params(params, 'taxa')).data) if params.get('with_taxa') else query
        query = query.with_trait_values(TraitValueParamsSerializer(self.fetch_filter_params(params, 'trait_values')).data) if params.get('with_trait_values') else query
        query = query.with_natural_occurrence_regions(NaturalOccurrenceRegionParamsSerializer(self.fetch_filter_params(params, 'natural_occurrence_regions')).data) if params.get('with_natural_occurrence_regions') else query
        # query = query.with_invasion_risk_regions(InvasionRiskRegionParamsSerializer(self.fetch_filter_params(params, 'invasion_risk_regions')).data) if params.get('with_invasion_risk_regions') else query

        return query

    def get(self, request, id):
        params = PlantParamsSerializer(request.query_params).data

        try:
            plant = self.get_queryset().get(id=id)
        except Plant.DoesNotExist:
            content = {'msg': 'Planta não encontrada.'}
            return Response(content, status=status.HTTP_404_NOT_FOUND)

        serializer = PlantSerializer(plant, params=params)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        data.update({'content_proposer_id': request.user.id})

        serializer = PlantCreationSerializer(data=data)
        try:
            plant = self.validate_and_save_serializer(serializer)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)

        content = {
            'plant_id': plant.id,
            'content_id': plant.content_id,
            'msg': 'Proposta cadastrada com sucesso.'
        }
    
        return Response(content, status=status.HTTP_201_CREATED)

class PlantListView(PlantView):
    def get(self, request):
        plants = self.get_queryset()

        serializer = PlantSerializer(
            plants,
            many=True,
            params=PlantParamsSerializer(request.query_params).data
        )

        return Response(serializer.data, status=status.HTTP_200_OK)
    

class PlantContentListView(ContentListView, ABC):
    def get(self, request, id):
        filters = self.params_serializer_class(request.query_params).data
        filters.update({'plant_id': id})

        objs = self.get_queryset().denormalized().filter(**filters)

        serializer = self.serializer_class(objs, many=True, content_params=self.get_content_params())

        return Response(serializer.data, status=status.HTTP_200_OK)


class TraitView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Trait.objects.denormalized()

    def get(self, request, trait_id):
        try:
            trait = self.get_queryset().get(id=trait_id)
        except Trait.DoesNotExist:
            return Response({'msg': 'Traço não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TraitSerializer(trait)

        return Response(serializer.data, status=status.HTTP_200_OK)

class TraitListView(TraitView):
    def get(self, request):
        filters = {'is_site_specific': False}
        filters.update(TraitParamsSerializer(request.query_params).data)

        traits = self.get_queryset().filter(**filters)

        serializer = TraitSerializer(traits, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class TraitValueView(ContentView):
    model_class = TraitValue
    serializer_class = TraitValueSerializer

class TraitValueListView(ContentListView):
    model_class = TraitValue
    serializer_class = TraitValueSerializer
    params_serializer_class = TraitValueParamsSerializer

class PlantTraitValueListView(PlantContentListView, TraitValueListView):
    pass


class PopularNameView(ContentView):
    model_class = PopularName
    serializer_class = PopularNameSerializer

class PopularNameListView(ContentListView):
    model_class = PopularName
    serializer_class = PopularNameSerializer
    params_serializer_class = PopularNameParamsSerializer    

class PlantPopularNameListView(PlantContentListView, PopularNameListView):
    pass


class TaxonView(ContentView):
    model_class = Taxon
    serializer_class = TaxonSerializer

class TaxonListView(ContentListView):
    model_class = Taxon
    serializer_class = TaxonSerializer
    params_serializer_class = TaxonParamsSerializer

class PlantTaxonListView(PlantContentListView, TaxonListView):
    pass


class NaturalOccurrenceRegionView(ContentView):
    model_class = NaturalOccurrenceRegion
    serializer_class = NaturalOccurrenceRegionSerializer

class NaturalOccurrenceRegionListView(ContentListView):
    model_class = NaturalOccurrenceRegion
    serializer_class = NaturalOccurrenceRegionSerializer
    params_serializer_class = NaturalOccurrenceRegionParamsSerializer

    def get_queryset(self):
        return super().get_queryset().only_important_fields()

class PlantNaturalOccurrenceRegionListView(PlantContentListView, NaturalOccurrenceRegionListView):
    pass
