from django.db.models.functions import Now
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from agroforestry.models import Farm, Field, SiteTrait, SiteTraitValue
from agroforestry.serializers import FarmSerializer, FieldSerializer, SiteTraitSerializer, SiteTraitValueSerializer
from agroforestry.services import delete_farm, delete_field, get_farm, get_field, get_site_owner_id, get_trait_value

class FarmView(APIView):
    def get_queryset(self):
        return Farm.objects.active().denormalized()

    def get(self, request, farm_id):
        try:
            farm = get_farm(farm_id, request.user.id)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)

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
    
    def put(self, request, farm_id):
        try:
            farm = get_farm(farm_id, request.user.id)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)

        data = request.data
        data.update({'user_id': request.user.id})

        serializer = FarmSerializer(farm, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            serializer.save()
        except Exception as err:
            return Response({'msg': err.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        content = {
            'msg': 'Propriedade atualizada com sucesso.'
        }
        
        return Response(content, status=status.HTTP_201_CREATED)
    
    def delete(self, request, farm_id):
        try:
            farm = get_farm(farm_id, request.user.id)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)
        
        try:
            delete_farm(farm)
        except Exception as err:
            return Response({'msg': err.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        content = {
            'msg': 'Propriedade removida com sucesso.'
        }
        
        return Response(content, status=status.HTTP_200_OK)

class FarmListView(FarmView):
    def get(self, request):
        farms = self.get_queryset().filter(user_id=request.user.id)

        serializer = FarmSerializer(farms, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class FieldView(APIView):
    def get_queryset(self):
        return Field.objects.active().denormalized()

    def get(self, request, field_id):
        try:
            field = get_field(field_id, request.user.id)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)

        serializer = FieldSerializer(field)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        data = request.data
        data.update({'user_id': request.user.id})

        serializer = FieldSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            object = serializer.save()
        except Exception as err:
            return Response({'msg': err.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        content = {
            'field_id': object.id,
            'site_id': object.site_id,
            'msg': 'Área cadastrada com sucesso.'
        }
        
        return Response(content, status=status.HTTP_201_CREATED)
    
    def put(self, request, field_id):
        try:
            field = get_field(field_id, request.user.id)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)

        data = request.data
        data.update({'user_id': request.user.id})

        serializer = FieldSerializer(field, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            serializer.save()
        except Exception as err:
            return Response({'msg': err.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        content = {
            'msg': 'Área atualizada com sucesso.'
        }
        
        return Response(content, status=status.HTTP_201_CREATED)
    
    def delete(self, request, field_id):
        try:
            field = get_field(field_id, request.user.id)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)
        
        try:
            delete_field(field)
        except Exception as err:
            return Response({'msg': err.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        content = {
            'msg': 'Área removida com sucesso.'
        }
        
        return Response(content, status=status.HTTP_200_OK)

class FieldListView(FieldView):
    def get(self, request, farm_id):
        fields = self.get_queryset().filter(user_id=request.user.id, farm_id=farm_id)

        serializer = FieldSerializer(fields, many=True)

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
    
    def get(self, request, site_trait_value_id):
        try:
            trait_value = get_trait_value(site_trait_value_id, request.user.id)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)

        serializer = SiteTraitValueSerializer(trait_value)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SiteTraitValueSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.user.id != get_site_owner_id(serializer.site):
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

    def put(self, request, site_trait_value_id):
        try:
            trait_value = get_trait_value(site_trait_value_id, request.user.id)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)
        
        serializer = SiteTraitValueSerializer(trait_value, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.user.id != get_site_owner_id(serializer.site):
            return Response({
                'msg': 'Você não tem autorização para publicar informações referentes a esse local.'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            object = serializer.save()
        except Exception as err:
            return Response({'msg': err.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        content = {
            'site_trait_value_id': object.id,
            'msg': 'Informação atualizada com sucesso.'
        }
        
        return Response(content, status=status.HTTP_201_CREATED)
    
    def delete(self, request, site_trait_value_id):
        try:
            trait_value = get_trait_value(site_trait_value_id, request.user.id)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)
        
        try:
            trait_value.deleted_at = Now()
            trait_value.save()
        except Exception as err:
            return Response({'msg': err.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        content = {
            'msg': 'Informação removida com sucesso.'
        }
        
        return Response(content, status=status.HTTP_200_OK)

class SiteTraitValueListView(SiteTraitValueView):
    def get(self, request, site_id):
        trait_values = self.get_queryset().filter(site_id=site_id)
        serializer = SiteTraitValueSerializer(trait_values, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
class FarmTraitValueListView(SiteTraitValueListView):
    def get(self, request, farm_id):
        try:
            farm = get_farm(farm_id, request.user.id)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)
        
        return super().get(request, farm.site_id)
    
class FieldTraitValueListView(SiteTraitValueListView):
    def get(self, request, field_id):
        try:
            farm = get_field(field_id, request.user.id)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)
        
        return super().get(request, farm.site_id)
