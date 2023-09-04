from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from users.models import CustomUser

from .models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                     RecipeTag, ShoppingList, Tag)
from .utils import decode_image


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount')


class RecipeTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeTag
        fields = ('tag',)


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )
    ingredients = RecipeIngredientSerializer(source='recipe_ingredients',
                                             many=True)
    tags = RecipeTagSerializer(source='recipe_tags', many=True)
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'image', 'text',
                  'cooking_time', 'tags', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart')

    def to_internal_value(self, data):
        image = data.get('image')
        data['image'] = decode_image(image, data.get('name'))
        return super().to_internal_value(data)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('recipe_tags')
        recipe = Recipe.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **ingredient_data)

        for tag_data in tags_data:
            RecipeTag.objects.create(recipe=recipe, **tag_data)

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.save()

        RecipeIngredient.objects.filter(recipe=instance).delete()
        RecipeTag.objects.filter(recipe=instance).delete()

        ingredients_data = validated_data.pop('recipe_ingredients', [])
        tags_data = validated_data.pop('recipe_tags', [])

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(recipe=instance, **ingredient_data)

        for tag_data in tags_data:
            RecipeTag.objects.create(recipe=instance, **tag_data)

        return instance

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return FavoriteRecipe.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return ShoppingList.objects.filter(user=user, recipe=obj).exists()


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteRecipe
        fields = ('id', 'user', 'recipe')


class ShoppingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = ('id', 'user', 'recipe')
