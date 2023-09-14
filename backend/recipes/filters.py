from django_filters import rest_framework as filters

from .models import FavoriteRecipe, ShoppingList, Recipe, Ingredient


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_by_relation')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_by_relation')
    author = filters.NumberFilter(field_name='author__id')
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = []

    def filter_by_relation(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset

        if value:
            model_map = {
                'is_favorited': FavoriteRecipe,
                'is_in_shopping_cart': ShoppingList,
            }
            filter_parameters = {"user": self.request.user}
            ids = model_map[name].objects.filter(**filter_parameters)\
                                         .values_list('recipe_id', flat=True)

            return queryset.filter(id__in=ids)
        return queryset


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
