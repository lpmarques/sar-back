from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from agroforestry.models import Farm, Field, Site, SiteTrait, SiteTraitValue
from agroforestry.serializers import FarmSerializer, SiteTraitSerializer, SiteTraitValueSerializer

class FarmView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Farm.objects.active().denormalized()

    def get(self, request, site_id):
        try:
            farm = self.get_queryset().get(site_id=site_id)
        except Farm.DoesNotExist:
            return Response({'msg': 'Propriedade não cadastrada.'}, status=status.HTTP_404_NOT_FOUND)
        
        if farm.site.deleted_at:
            return Response({'msg': 'Propriedade indisponível.'}, status=status.HTTP_404_NOT_FOUND)
        
        if farm.user_id != request.user.id:
            return Response({'msg': 'Você não tem autorização para acessar essa propriedade.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = FarmSerializer(farm)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        data = request.data
        data.update({'user_id': request.user.id})

        serializer = FarmSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            object = serializer.save()
        except Exception as err:
            return Response({'msg': err.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        content = {
            'farm_id': object.id,
            'site_id': object.site_id,
            'msg': 'Propriedade cadastrada com sucesso.'
        }
        
        return Response(content, status=status.HTTP_201_CREATED)
    
    # def delete(self, request):
    #     # TODO
    #     # ao deletar o site, deletar todos os seus site_trait_values

class FarmListView(FarmView):
    def get(self, request):
        farms = self.get_queryset().filter(user_id=request.user.id)

        serializer = FarmSerializer(farms, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class SiteTraitListView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return SiteTrait.objects.denormalized()

    def get(self, request):
        site_traits = self.get_queryset()

        serializer = SiteTraitSerializer(site_traits, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class SiteTraitValueView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SiteTraitValue.objects.active().denormalized()
    
    def get_site_owner_id(self, site: Site):
        if site.TYPE.FRM:
            return Farm.objects.get(site_id=site.id).user_id
        else:
            return Field.objects.get(site_id=site.id).farm.user_id
    
    def get(self, request, site_trait_value_id):
        try:
            trait_value = self.get_queryset().get(id=site_trait_value_id)
        except SiteTraitValue.DoesNotExist:
            return Response({'msg': 'Informação não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.id != self.get_site_owner_id(trait_value.site):
            return Response({
                'msg': 'Você não tem autorização para acessar essa informação.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = SiteTraitValueSerializer(trait_value)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SiteTraitValueSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.user.id != self.get_site_owner_id(serializer.site):
            return Response({
                'msg': 'Você não tem autorização para publicar informações referentes a esse local.'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            object = serializer.save()
        except Exception as err:
            return Response({'msg': err.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        content = {
            'site_trait_value_id': object.id,
            'msg': 'Informação publicada com sucesso.'
        }
        
        return Response(content, status=status.HTTP_201_CREATED)
    
    # def delete(self, request, site_trait_value_id):
    #     # TODO

    
class SiteTraitValueListView(SiteTraitValueView):
    def get(self, request, site_id):
        try:
            site = Site.objects.get(id=site_id)
        except Site.DoesNotExist:
            return Response({'msg': 'Local não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.id != self.get_site_owner_id(site):
            return Response({
                'msg': 'Você não tem autorização para acessar essas informações.'
            }, status=status.HTTP_403_FORBIDDEN)

        trait_values = self.get_queryset().filter(site_id=site_id)
        serializer = SiteTraitValueSerializer(trait_values, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    