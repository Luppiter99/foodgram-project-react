from django.contrib.auth import get_user_model
from django.http import HttpResponse

from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import CustomUser, Subscription
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from api.serializers import (
    CustomUserCreateSerializer,
    CustomUserSerializer,
    CustomUserWithRecipesSerializer,
    IngredientSerializer,
    RecipeIngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    FavoriteRecipe,
    ShoppingList
)
from recipes.filters import RecipeFilter, IngredientFilter
from .pagination import CustomUserPagination


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

        user = self.request.user
        author = self.get_object()

        subscription = user.following.filter(author=author)
        if not subscription.exists():
            return Response({'error': 'Not subscribed'},
                            status=status.HTTP_400_BAD_REQUEST)

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        recipes_limit = request.query_params.get('recipes_limit', None)
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                return Response({'error': 'Invalid recipes_limit value'},
                                status=status.HTTP_400_BAD_REQUEST)

        subscriptions = (Subscription.objects.filter(user=request.user)
                         .prefetch_related('author', 'author__recipes'))
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = CustomUserWithRecipesSerializer(
                [sub.author for sub in page],
                many=True,
                context={
                    'request': request,
                    'recipes_limit': recipes_limit}
            )
            return self.get_paginated_response(serializer.data)

        serializer = CustomUserWithRecipesSerializer(
            [sub.author for sub in subscriptions],
            many=True,
            context={
                'request': request,
                'recipes_limit': recipes_limit}
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


class TokenLogoutConfirmationView(APIView):
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
    queryset = Recipe.objects.all().order_by('-pub_date')
    serializer_class = RecipeReadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def manage_relation(self, request, model, action_type, pk=None):
        recipe = self.get_object()
        if action_type == 'create':
            model.objects.get_or_create(user=request.user, recipe=recipe)
            return Response(status=status.HTTP_201_CREATED)
        model.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST', 'DELETE'], url_path='favorite')
    def manage_favorites(self, request, pk=None):
        if request.method == 'POST':
            self.manage_relation(request, FavoriteRecipe, 'create', pk)
            return Response({"detail": "Recipe added to favorites."},
                            status=status.HTTP_201_CREATED)
        self.manage_relation(request, FavoriteRecipe, 'delete', pk)
        return Response({"detail": "Recipe removed from favorites."},
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST', 'DELETE'], url_path='shopping_cart')
    def manage_shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            self.manage_relation(request, ShoppingList, 'create', pk)
            return Response({"detail": "Recipe added to shopping cart."},
                            status=status.HTTP_201_CREATED)
        self.manage_relation(request, ShoppingList, 'delete', pk)
        return Response({"detail": "Recipe removed from shopping cart."},
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        shopping_list_recipes = (
            ShoppingList.objects.filter(user=user).values_list('recipe',
                                                               flat=True)
        )
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=shopping_list_recipes
        )

        aggregated_ingredients = {}
        for ingredient in ingredients:
            key = (
                ingredient.ingredient.name,
                ingredient.ingredient.measurement_unit
            )
            if key not in aggregated_ingredients:
                aggregated_ingredients[key] = 0
            aggregated_ingredients[key] += ingredient.amount

        ingredients_list = []
        for (name, unit), amount in aggregated_ingredients.items():
            ingredients_list.append(f"{name} ({unit}) — {amount}")

        response = HttpResponse('\n'.join(ingredients_list),
                                content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return RecipeWriteSerializer
        return RecipeReadSerializer


class RecipeIngredientViewSet(viewsets.ModelViewSet):
    queryset = RecipeIngredient.objects.all()
    serializer_class = RecipeIngredientSerializer
