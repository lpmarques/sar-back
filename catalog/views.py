from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import Now
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.views import ContentView
from catalog.models import Plant, NaturalOccurrenceRegion, PopularName, Taxon, TraitValue
from catalog.serializers.models import *
from catalog.serializers.parameters import *

class PlantView(APIView):
    permission_classes = [AllowAny]

    def fetch_filter_params(self, params_data: dict, related_name: str):
        return { key.replace(f'{related_name}_', ''): value for key, value in params_data.items() if f'{related_name}_' in key }

    def get_queryset(self):
        params = PlantParamsSerializer(self.request.query_params).data

        query = Plant.objects.denormalized()
        query = query.with_popular_names(PopularNameParamsSerializer(self.fetch_filter_params(params, 'popular_names')).data) if params.get('with_popular_names') else query
        query = query.with_taxa(TaxonParamsSerializer(self.fetch_filter_params(params, 'taxa')).data) if params.get('with_taxa') else query
        query = query.with_trait_values(TraitValueParamsSerializer(self.fetch_filter_params(params, 'trait_values')).data) if params.get('with_trait_values') else query
        query = query.with_natural_occurrence_regions(NaturalOccurrenceRegionParamsSerializer(self.fetch_filter_params(params, 'natural_occurrence_regions')).data) if params.get('with_natural_occurrence_regions') else query
        # query = query.with_invasion_risk_regions(InvasionRiskRegionParamsSerializer(self.fetch_filter_params(params, 'invasion_risk_regions')).data) if params.get('with_invasion_risk_regions') else query

        return query

    def get(self, request, plant_id):
        params = PlantParamsSerializer(request.query_params)

        try:
            plant = self.get_queryset().get(id=plant_id)
        except Plant.DoesNotExist:
            content = {'msg': 'Planta não encontrada.'}
            return Response(content, status=status.HTTP_404_NOT_FOUND)

        serializer = PlantSerializer(plant, params=params.data)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PlantListView(PlantView):
    def get(self, request):
        filters = PlantParamsSerializer(self.fetch_filter_params(request.query_params, 'plant')).data
        plants = self.get_queryset().filter(**filters)

        serializer = PlantSerializer(plants, many=True, params=PlantParamsSerializer(request.query_params).data)

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
    permission_classes = [IsAuthenticated]
    serializer_class = TraitValueSerializer


class PlantTraitValueListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, plant_id):
        filters = TraitValueParamsSerializer(request.query_params).data
        filters.update({'plant_id': plant_id})

        try:
            plant = Plant.objects.get(id=plant_id)
            trait_values = TraitValue.objects.denormalized().filter(**filters)
        except Plant.DoesNotExist:
            content = {'msg': 'Planta não cadastrada'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = PlantTraitValueSerializer(trait_values, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PopularNameView(ContentView):
    permission_classes = [IsAuthenticated]
    serializer_class = PopularNameSerializer


class PopularNameListView(APIView):
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        filters = PopularNameParamsSerializer(self.request.query_params).data

        return PopularName.objects.filter(**filters)

    def get(self, request):
        popular_names = self.get_queryset().denormalized()
        serializer = PopularNameSerializer(popular_names, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    

class PlantPopularNameListView(PopularNameListView):
    def get(self, request, plant_id):
        try:
            plant = Plant.objects.get(id=plant_id)
            popular_names = self.get_queryset().denormalized().filter(plant_id=plant.id)
        except Plant.DoesNotExist:
            content = {'msg': 'Planta não cadastrada'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = PopularNameSerializer(popular_names, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class TaxonView(ContentView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaxonSerializer


class TaxonListView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        filters = TaxonParamsSerializer(self.request.query_params).data

        return Taxon.objects.filter(**filters)

    def get(self, request):
        taxa = self.get_queryset().denormalized()
        serializer = TaxonSerializer(taxa, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PlantTaxonListView(TaxonListView):
    def get(self, request, plant_id):
        try:
            plant = Plant.objects.get(id=plant_id)
            taxa = self.get_queryset().denormalized().filter(plant_id=plant_id)
        except Plant.DoesNotExist:
            content = {'msg': 'Planta não cadastrada'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PlantTaxonSerializer(taxa, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class NaturalOccurrenceRegionListView(ContentView):
    permission_classes = [IsAuthenticated]
    serializer_class = NaturalOccurrenceRegionSerializer


class NaturalOccurrenceRegionListView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        filters = NaturalOccurrenceRegionParamsSerializer(self.request.query_params).data
        return NaturalOccurrenceRegion.objects.denormalized().only_important_fields().filter(**filters)
        
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
