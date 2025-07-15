import pandas as pd
from django.db.models import Prefetch
from django.db.models.expressions import RawSQL
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from catalog.models import Plant, PlantPopularName, PlantScientificName
from catalog.serializers import PlantSerializer, PopularNameSerializer, ScientificNameSerializer


class PlantListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plants = Plant.objects.all()
        serializer = PlantSerializer(plants, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
  
class PlantView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, plant_id):
        try:
            country = Plant.objects.get(id=plant_id, content_status='accepted')
        except Plant.DoesNotExist:
            content = {'msg': 'Planta não cadastrada'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        serializer = PlantSerializer(country)

        return Response(serializer.data, status=status.HTTP_200_OK)

class PopularNameListView(APIView):
    permission_classes = [AllowAny]

    def group_by_popular_name(self, list):
        grouped_df = pd.DataFrame(list).groupby('name')['plant'].apply(list)
        
        return grouped_df.reset_index(name='plants').to_dict(orient='records')

    def get(self, request):
        popular_names = PlantPopularName.objects.filter(content_status='accepted').select_related('plant')
        serializer = PopularNameSerializer(popular_names, many=True)
        
        data = self.group_by_popular_name(serializer.data) # TODO: consider changing relation to M2M and removing this step

        return Response(data, status=status.HTTP_200_OK)

class ScientificNameListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        scientific_names = PlantScientificName.objects.filter(content_status='accepted').prefetch_related(
            Prefetch('plant', queryset=Plant.objects.filter(content_status='accepted').prefetch_related(
                Prefetch('popular_names', queryset=PlantPopularName.objects.filter(content_status='accepted'))
            ))
        )
        # scientific_names = PlantScientificName.objects.filter(content_status='accepted').prefetch_related('plant__popular_names')
        serializer = ScientificNameSerializer(scientific_names, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
