from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Tag
from .serializers import (FavoriteRecipe, IngredientSerializer,
                          RecipeIngredientSerializer, RecipeSerializer,
                          RecipeTagSerializer, ShoppingList, TagSerializer)


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')
    author = filters.NumberFilter(field_name='author__id')
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = []

    def filter_is_favorited(self, queryset, name, value):
        if value:
            fav_ids = FavoriteRecipe.objects.filter(
                user=self.request.user
            ).values_list('recipe_id', flat=True)
            return queryset.filter(id__in=fav_ids)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            cart_ids = ShoppingList.objects.filter(
                user=self.request.user
            ).values_list('recipe_id', flat=True)
            return queryset.filter(id__in=cart_ids)
        return queryset


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    http_method_names = ['get']


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all().order_by('id')
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('id')
    serializer_class = RecipeSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['POST'], url_path='favorite')
    def add_to_favorites(self, request, pk=None):
        recipe = self.get_object()
        FavoriteRecipe.objects.get_or_create(user=request.user, recipe=recipe)
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['DELETE'], url_path='favorite')
    def remove_from_favorites(self, request, pk=None):
        recipe = self.get_object()
        FavoriteRecipe.objects.filter(user=request.user,
                                      recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'], url_path='shopping_cart')
    def add_to_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        ShoppingList.objects.get_or_create(user=request.user, recipe=recipe)
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['DELETE'], url_path='shopping_cart')
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        ShoppingList.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeIngredientViewSet(viewsets.ModelViewSet):
    queryset = RecipeIngredient.objects.all().order_by('id')
    serializer_class = RecipeIngredientSerializer


class RecipeTagViewSet(viewsets.ModelViewSet):
    queryset = RecipeTag.objects.all().order_by('id')
    serializer_class = RecipeTagSerializer
