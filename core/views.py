from django.contrib.auth import authenticate
from django.db.models.functions import Now
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import User, ContentEndorsement, Source
from core.permissions import IsOwnUser
from core.serializers import *

class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            content = {'msg': 'Usuário não cadastrado.'}
            return Response(content, status=status.HTTP_404_NOT_FOUND)

        if user.deleted_at:
            content = {'msg': 'Dados indisponíveis.'}
            return Response(content, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)


class OwnUserView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]

        return [IsOwnUser()]

    def get(self, request):
        serializer = UserSerializer(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserCreationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            pass
        else:
            content = {'msg': ('E-mail já cadastrado.')}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(email=email)
        user.set_password(serializer.data.get('password'))
        user.first_name = serializer.data.get('first_name')
        user.last_name = serializer.data.get('last_name')
        user.occupation = serializer.data.get('occupation')
        user.company = serializer.data.get('company')
        user.country = serializer.data.get('country')
        user.state = serializer.data.get('state')
        user.municipality = serializer.data.get('municipality')
        user.save()

        content = {
            'msg': ('Usuário cadastrado com sucesso.')
        }

        return Response(content, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.data['email']
        try:
            user = User.objects.get(email=email)
            self.check_object_permissions(self.request, user)
        except User.DoesNotExist:
            content = {'msg': 'Usuário não existe.'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        user.first_name = serializer.data.get('first_name')
        user.last_name = serializer.data.get('last_name')
        user.occupation = serializer.data.get('occupation')
        user.company = serializer.data.get('company')
        user.country = serializer.data.get('country')
        user.state = serializer.data.get('state')
        user.municipality = serializer.data.get('municipality')

        user.save()

        content = {
            'msg': ('Dados do usuário atualizados com sucesso.')
        }

        return Response(content, status=status.HTTP_200_OK)
    
    def delete(self, request):
        request.user.anonymize()

        tokens = Token.objects.filter(user=request.user)
        for token in tokens:
            token.delete()

        content = {
            'msg': ('Dados do usuário removidos com sucesso.')
        }
        
        return Response(content, status=status.HTTP_200_OK)


class UserTokenView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]

        return [IsAuthenticated()]

    def post(self, request):
        serializer = UserTokenCreationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.data.get('email')
        password = serializer.data.get('password')

        user = authenticate(email=email, password=password)
        if not user or user.deleted_at:
            content = {'msg': ('E-mail ou senha inválidos.')}
            return Response(content, status=status.HTTP_401_UNAUTHORIZED)
                
        token, created = Token.objects.get_or_create(user=user)
        content = {
            'token': token.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name 
            },
            'msg': ('Login realizado com sucesso.')
        }

        return Response(content, status=status.HTTP_200_OK)

    def delete(self, request):
        tokens = Token.objects.filter(user=request.user)
        for token in tokens:
            token.delete()

        content = {'msg': ('Logout realizado com sucesso.')}

        return Response(content, status=status.HTTP_200_OK)


class ContentEndorsementView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        data.update({'endorser_id': request.user.id})
        serializer = ContentEndorsementSerializer(data=data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            endorsement = serializer.save()
        except Exception as err:
            return Response({'msg': err.args[0]}, status=status.HTTP_400_BAD_REQUEST)

        content = {
            'endorsement_id': endorsement.id,
            'msg': 'Conteúdo aprovado com sucesso.'
        }
    
        return Response(content, status=status.HTTP_201_CREATED)
    
    def delete(self, request, endorsement_id):
        try:
            endorsement = ContentEndorsement.objects.denormalized().get(id=endorsement_id)
        except ContentEndorsement.DoesNotExist:
            return Response({'msg': 'Não há aprovação cadastrada com esse id.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if endorsement.endorser.id != request.user.id:
            return Response({'msg': 'Você não tem autorização para remover essa aprovação.'}, status=status.HTTP_401_UNAUTHORIZED)

        if endorsement.deleted_at:
            return Response({'msg': 'Aprovação já removida.'}, status=status.HTTP_400_BAD_REQUEST)

        endorsement.deleted_at = Now()
        endorsement.content.endorsements -= 1
        endorsement.content.save()
        endorsement.save()

        content = {
            'msg': 'Aprovação removida com sucesso.'
        }
    
        return Response(content, status=status.HTTP_200_OK)
    

class ContentEndorsementListView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        filters = ContentEndorsementParamsSerializer(self.request.query_params).data

        return ContentEndorsement.objects.active().filter(**filters)

    def get(self, request):
        endorsements = self.get_queryset().denormalized()
        serializer = ContentEndorsementSerializer(endorsements, many=True)
    
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UserContentEndorsementListView(ContentEndorsementListView):
    def get(self, request):
        endorsements = self.get_queryset().filter(endorser_id=request.user.id)

        serializer = UserContentEndorsementSerializer(endorsements, many=True)
    
        return Response(serializer.data, status=status.HTTP_200_OK)


class SourceView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]

        return [IsAuthenticated()]

    def get(self, request, source_id):
        try:
            source = Source.objects.denormalized().get(id=source_id)
        except Source.DoesNotExist:
            return Response({'msg': 'Não há fonte cadastrada com esse id.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SourceSerializer(source)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        data.update({'creator_id': request.user.id})
        # data.update({'creator_id': 4})
        serializer = SourceSerializer(data=data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            source = serializer.save()
        except Exception as err:
            return Response({'msg': err.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        content = {
            'source_id': source.id,
            'msg': 'Fonte cadastrada com sucesso.'
        }
    
        return Response(content, status=status.HTTP_201_CREATED)


class SourceListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        sources = Source.objects.denormalized().active()
        serializer = SourceSerializer(sources, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    

class SourceTypeListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, type_id=None):
        filters = {
            "level": SourceType.Level.SUBTYPE,
            "parent_id": type_id
        } if type_id else {
            "level": SourceType.Level.TYPE
        }

        source_types = SourceType.objects.denormalized().active().filter(**filters)
        serializer = SourceTypeSerializer(source_types, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    