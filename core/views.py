from django.contrib import messages
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import User
from core.permissions import IsOwnUser
from core.serializers import UserSerializer, UserCreationSerializer, UserUpdateSerializer, UserTokenCreationSerializer

@api_view(['GET'])
def getRoutes(request):
    routes = [
        # 'GET /core',
        # 'GET /core/user',
        # 'GET /core/user/:id',
        # 'POST /core/user/signup/',
        # 'POST /core/user/login/',
        # 'POST /core/user/logout/',
    ]

    return JsonResponse(routes, safe=False)


class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            user = User.objects.get(id=id)
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
        user.country_id = serializer.data.get('country_id')
        user.state_id = serializer.data.get('state_id')
        user.municipality_id = serializer.data.get('municipality_id')
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
        user.country_id = serializer.data.get('country_id')
        user.state_id = serializer.data.get('state_id')
        user.municipality_id = serializer.data.get('municipality_id')

        user.save()

        content = {
            'msg': ('Dados do usuário atualizados com sucesso.')
        }

        return Response(content, status=status.HTTP_200_OK)
    
    def delete(self, request):
        request.user.anonymize()

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

        content = {'success': ('Logout realizado com sucesso.')}

        return Response(content, status=status.HTTP_200_OK)
