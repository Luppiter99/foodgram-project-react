from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1  # Количество пустых форм для добавления


class RecipeTagInline(admin.TabularInline):
    model = Recipe.tags.through
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorite_count')
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'name', 'tags')
    inlines = [RecipeIngredientInline, RecipeTagInline]

    def favorite_count(self, obj):
        return obj.favorited_by.count()

    def save_model(self, request, obj, form, change):
        if change:
            if not obj.recipe_ingredients.all():
                raise ValidationError(
                    "Рецепт должен иметь хотя бы один ингредиент!"
                )
        super().save_model(request, obj, form, change)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'tag')
