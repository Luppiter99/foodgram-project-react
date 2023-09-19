from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect

from .models import (
    Ingredient, Recipe, RecipeIngredient, RecipeTag, Tag,
    FavoriteRecipe)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


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
        return FavoriteRecipe.objects.filter(recipe=obj).count()

    def changeform_view(self, request, object_id=None, form_url='',
                        extra_context=None):
        if request.method == 'POST':
            change = object_id is not None
            formsets, inline_instances = self._create_formsets(
                request, None, change
            )
            ingredients_formset = None
            for formset, inline in zip(formsets, inline_instances):
                if isinstance(inline, RecipeIngredientInline):
                    ingredients_formset = formset
                    break

            if ingredients_formset and not any(
                form.is_valid() and form.has_changed()
                for form in ingredients_formset
            ):
                messages.error(
                    request,
                    "Рецепт должен иметь хотя бы один ингредиент!"
                )
                return HttpResponseRedirect(request.path)

        return super().changeform_view(request, object_id, form_url,
                                       extra_context)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'tag')
