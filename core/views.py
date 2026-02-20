from abc import ABC, abstractmethod
from django.contrib.auth import authenticate
from django.db.models import Q
from django.db.models.functions import Now
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import User, ContentEndorsement, Source
from core.permissions import IsOwnUser
from core.serializers import *

class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None):
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                content = {'msg': 'Usuário não cadastrado.'}
                return Response(content, status=status.HTTP_404_NOT_FOUND)
        else:
            email = request.query_params.get('email')
            if not email:
                content = {'email': 'Parâmetro obrigatório.'}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)
            try:
                user = User.objects.get(email=email)
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
                'last_name': user.last_name,
                'is_staff': user.is_staff,
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


class ContentView(APIView, ABC):
    @property
    @abstractmethod
    def model_class(self): # sets model_class as abstract attribute that needs to be declared in child
        pass

    @property
    @abstractmethod
    def serializer_class(self):
        pass

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]

        return [IsAuthenticated()]

    def get_content_params(self):
        params = ContentParamsSerializer(self.request.query_params).data if self.request.query_params else {}
        if not self.request.user.is_authenticated:
            params.pop('with_user_endorsement_info', {})

        return params

    def get_queryset(self):
        query = self.model_class.objects
        if self.get_content_params().get('with_user_endorsement_info'):
            query = query.with_user_endorsement_info(self.request.user)

        return query

    def validate_and_save_serializer(self, serializer: ModelSerializer):
        serializer.is_valid(raise_exception=True)

        return serializer.save()

    def get(self, request, id):
        try:
            obj = self.get_queryset().denormalized().get(id=id)
        except self.model_class.DoesNotExist:
            return Response({'msg': 'Objeto não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(obj, self.get_content_params())

        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def post(self, request):
        data = request.data
        data.update({'content_proposer_id': request.user.id})
        serializer = self.serializer_class(data=data)

        try:
            obj = self.validate_and_save_serializer(serializer)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)

        content = {
            'id': obj.id,
            'content_id': obj.content_id,
            'msg': 'Proposta cadastrada com sucesso.'
        }

        return Response(content, status=status.HTTP_201_CREATED)

    def patch(self, request, id):
        try:
            obj = self.get_queryset().get(id=id)
        except self.model_class.DoesNotExist:
            return Response({'msg': 'Proposta não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        
        if obj.content.status != "proposed":
            return Response({'msg': 'Essa proposta já foi aceita ou rejeitada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not request.user.is_staff:
            return Response({'msg': 'Você não tem permissão para aceitar essa proposta.'}, status=status.HTTP_403_FORBIDDEN)

        # partial update in object serializer accepts the proposal
        serializer = self.serializer_class(
            obj,
            data={'content_acceptor_id': request.user.id},
            partial=True
        )

        try:
            accepted_obj = self.validate_and_save_serializer(serializer)
        except APIException as err:
            return Response({'msg': err.detail}, status=err.status_code)

        content = {
            'msg': 'Proposta aprovada com sucesso.'
        }

        return Response(content, status=status.HTTP_201_CREATED)
    
    def delete(self, request, id):
        try:
            obj = self.get_queryset().get(id=id)
        except self.model_class.DoesNotExist:
            return Response({'msg': 'Proposta não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        
        if obj.content.status != "proposed":
            return Response({'msg': 'Essa proposta já foi aceita ou rejeitada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if obj.content.proposer_id != request.user.id and not request.user.is_staff:
            return Response({'msg': 'Você não tem permissão para rejeitar essa proposta.'}, status=status.HTTP_403_FORBIDDEN)

        obj.content.status = "rejected"
        obj.content.rejected_at = Now()
        obj.content.rejector_id = request.user.id
        obj.content.save()

        content = {
            'msg': 'Proposta rejeitada com sucesso.'
        }
    
        return Response(content, status=status.HTTP_200_OK)

class ContentListView(ContentView, ABC):
    @property
    @abstractmethod
    def params_serializer_class(self): # sets params_serializer_class as abstract attribute that needs to be declared in child
        pass

    def get_filter_params(self):
        return self.params_serializer_class(self.request.query_params).data
        
    def get(self, request):
        objs = self.get_queryset().denormalized().filter(**self.get_filter_params())

        serializer = self.serializer_class(objs, many=True, content_params=self.get_content_params())

        return Response(serializer.data, status=status.HTTP_200_OK)


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
            'msg': 'Conteúdo apoiado com sucesso.'
        }
    
        return Response(content, status=status.HTTP_201_CREATED)
    
    def delete(self, request, endorsement_id):
        try:
            endorsement = ContentEndorsement.objects.denormalized().get(id=endorsement_id)
        except ContentEndorsement.DoesNotExist:
            return Response({'msg': 'Não há apoio cadastrado com esse id.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if endorsement.endorser.id != request.user.id:
            return Response({'msg': 'Você não tem permissão para remover esse apoio.'}, status=status.HTTP_403_FORBIDDEN)

        if endorsement.deleted_at:
            return Response({'msg': 'Apoio já removido.'}, status=status.HTTP_400_BAD_REQUEST)

        endorsement.deleted_at = Now()
        endorsement.content.endorsements_count -= 1
        endorsement.content.save()
        endorsement.save()

        content = {
            'msg': 'Apoio removido com sucesso.'
        }
    
        return Response(content, status=status.HTTP_200_OK)
    

class ContentEndorsementListView(ContentEndorsementView):
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


class SourceListView(SourceView):
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

class ContentPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Content.objects.select_related(
            'proposer'
        ).filter(
            ~Q(proposer__email='perma.lucas@gmail.com') # TODO: think less ugly solution to this
        )

    def get(self, request, content_id):
        try:
            content = self.get_queryset().get(id=content_id)
        except Content.DoesNotExist:
            return Response({'msg': 'Conteúdo não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ContentPreviewSerializer(content)

        return Response(serializer.data, status=status.HTTP_200_OK)

class ContentPreviewListView(ContentPreviewView):
    def get(self, request):
        filters = ContentPreviewParamsSerializer(self.request.query_params).data
        
        contents = self.get_queryset().filter(**filters)
        serializer = ContentPreviewSerializer(contents, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
