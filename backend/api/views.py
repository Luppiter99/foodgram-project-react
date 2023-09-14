from django.contrib.auth import get_user_model
from django.http import HttpResponse

from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import PermissionDenied

from users.models import CustomUser, Subscription
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from api.serializers import (
    CustomUserCreateSerializer,
    CustomUserSerializer,
    CustomUserWithRecipesSerializer,
    IngredientSerializer,
    RecipeIngredientSerializer,
    RecipeSerializer,
    TagSerializer,
    FavoriteRecipe,
    ShoppingList
)
from recipes.filters import RecipeFilter, IngredientFilter


class CustomUserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 1000


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomUserPagination

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = CustomUserSerializer(request.user,
                                          context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = CustomUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_data = CustomUserCreateSerializer(user).data
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['POST', 'DELETE'], url_path='subscribe',
            permission_classes=[IsAuthenticated])
    def manage_subscription(self, request, pk=None):
        if request.method == 'POST':
            user = self.request.user
            author = self.get_object()

            if user.id == author.id:
                return Response({'error': 'Cannot subscribe to yourself'},
                                status=status.HTTP_400_BAD_REQUEST)

            Subscription.objects.get_or_create(user=user, author=author)
            serializer = CustomUserWithRecipesSerializer(
                author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            user = self.request.user
            author = self.get_object()

            subscription = Subscription.objects.filter(user=user,
                                                       author=author)
            if not subscription.exists():
                return Response({'error': 'Not subscribed'},
                                status=status.HTTP_400_BAD_REQUEST)

            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        subscriptions = Subscription.objects.filter(
            user=request.user
        ).prefetch_related('author', 'author__recipes')

        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = CustomUserWithRecipesSerializer(
                [sub.author for sub in page],
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = CustomUserWithRecipesSerializer(
            [sub.author for sub in subscriptions],
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({'error': 'Missing required fields'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({'error': 'Invalid current password'},
                            status=status.HTTP_401_UNAUTHORIZED)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password successfully changed'},
                        status=status.HTTP_204_NO_CONTENT)


class CustomTokenObtainPairView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email', None)
        password = request.data.get('password', None)

        if not email or not password:
            return Response({'detail': 'Email and password are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = get_user_model().objects.filter(email=email).first()

        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({'auth_token': str(refresh.access_token)},
                            status=status.HTTP_201_CREATED)

        return Response({'error': 'Invalid credentials'},
                        status=status.HTTP_401_UNAUTHORIZED)


class TokenDestroyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get']
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def manage_relation(self, request, model, action_type, pk=None):
        recipe = self.get_object()
        if action_type == 'create':
            model.objects.get_or_create(user=request.user, recipe=recipe)
            return Response(status=status.HTTP_201_CREATED)
        elif action_type == 'delete':
            model.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST', 'DELETE'], url_path='favorite')
    def manage_favorites(self, request, pk=None):
        if request.method == 'POST':
            self.manage_relation(request, FavoriteRecipe, 'create', pk)
            return Response({"detail": "Recipe added to favorites."},
                            status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            self.manage_relation(request, FavoriteRecipe, 'delete', pk)
            return Response({"detail": "Recipe removed from favorites."},
                            status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST', 'DELETE'], url_path='shopping_cart')
    def manage_shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            self.manage_relation(request, ShoppingList, 'create', pk)
            return Response({"detail": "Recipe added to shopping cart."},
                            status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            self.manage_relation(request, ShoppingList, 'delete', pk)
            return Response({"detail": "Recipe removed from shopping cart."},
                            status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        if self.get_object().author != self.request.user:
            raise PermissionDenied(
                "You can't update a recipe you didn't create!"
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied(
                "You can't delete a recipe you didn't create!"
            )
        instance.delete()

    @action(detail=False, methods=['GET'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        shopping_list = ShoppingList.objects.filter(user=user)
        ingredients_list = []

        for item in shopping_list:
            recipe = item.recipe
            recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)

            for ri in recipe_ingredients:
                ingredient = ri.ingredient
                ingredients_list.append(
                    f"{ingredient.name} - {ri.amount}"
                    f" {ingredient.measurement_unit}"
                )

        response = HttpResponse('\n'.join(ingredients_list),
                                content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


class RecipeIngredientViewSet(viewsets.ModelViewSet):
    queryset = RecipeIngredient.objects.all()
    serializer_class = RecipeIngredientSerializer
