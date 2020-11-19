from rest_framework import generics, views, permissions, response, status, parsers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from api.models import UserProfile, Item, Category, ItemImage
from api import serializers
from api import exceptions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.db.utils import IntegrityError


class ProfileListView(views.APIView):
    serializer_class = serializers.ProfileSerializer
    permissions_class = [permissions.IsAuthenticated]

    def get(self, request):
        print(self.request.user)
        profile = self.request.user.profile
        serializer = self.serializer_class(profile)
        return response.Response(serializers.data, 200)


class ItemListView(generics.ListCreateAPIView):
    serializer_class = serializers.ItemListSerializer
    permissions_classes = [permissions.IsAuthenticated]
    queryset = Item.objects.all()

    def get_queryset(self):
        return self.queryset.filter(creator=self.request.user.profile)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        val_data = serializer.validated_data
        creator = val_data.get('creator')

        if creator != self.request.user.profile:
            raise exceptions.InvalidUser()
        instance = serializer.save(creator=self.request.user.profile)
        return response.Response(self.serializer_class(instance).data, 201)


class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.ItemDetailSerializer
    permissions_classes = [permissions.IsAuthenticated]
    queryset = Item.objects.all()
    lookup_field = 'id'

    def get_queryset(self):
        return self.queryset.filter(creator=self.request.user.profile)

    def perform_update(self, serializer):
        serializer.save(creator=self.request.user.profile)


class ItemBatchDelete(views.APIView):
    serializer_class = serializers.BatchDeleteForm
    permissions_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = self.request.data
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        items = serializer.validated_data['items']
        for item in items:
            if item.creator != self.request.user.profile:
                raise exceptions.CantNotFound

        for item in items:
            item.delete()
        return response.Response({}, 201)


class CategoryListView(generics.ListCreateAPIView):
    serializer_class = serializers.CatListSerializer
    permissions_classes = [permissions.IsAuthenticated]
    queryset = Category.objects.all()

    def get_queryset(self, request=None):
        return self.queryset.filter(creator=self.request.user.profile)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        val_data = serializer.validated_data
        creator = val_data.get('creator')

        if creator != self.request.user.profile:
            raise exceptions.InvalidUser
        instance = serializer.save(creator=self.request.user.profile)
        return response.Response(self.serializer_class(instance).data, 201)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.CatDetailserializer
    permissions_classes = [permissions.IsAuthenticated]
    queryset = Category.objects.all()
    lookup_field = 'id'

    def get_queryset(self):
        return self.queryset.filter(creator=self.request.user.profile)


class UserRegister(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid(raise_exception=True):
            return response.Response({'error': 'not valid'})
        val_data = serializer.validated_data
        try:
            user = User.objects.create_user(username=val_data['account'], password=val_data['password'])
            profile = UserProfile.objects.create(user=user, name=val_data['username'])
        except:
            raise exceptions.UserExist

        return response.Response({'created success'}, 201)


class UserLogin(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        
        data = {
            'username': request.data.get('account'),
            'password': request.data.get('password')
        }
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            creator = user.profile
        except:
            raise exceptions.CantNotFound

        token, created = Token.objects.get_or_create(user=user)
        return response.Response({'userid': creator.id, 'username': creator.name, 'token': token.key})


class ImageUploadView(views.APIView):
    host = "https://todolist.revtel2.com"
    parser_class = (parsers.FileUploadParser,)
    serializer_class = serializers.ItemImageSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            data = serializer.data.copy()
            data['image'] = self.host + data['image']
            return response.Response(data, 201)
        else:
            return response.Response(serializer.errors, 400)
