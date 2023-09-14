from rest_framework import serializers

from recipes.models import (
    FavoriteRecipe, Ingredient, Recipe,
    RecipeIngredient, ShoppingList, Tag
)
from recipes.utils import decode_image
from users.models import CustomUser, Subscription


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email',
                  'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            subscription_exists = Subscription.objects.filter(
                user=user,
                author=obj
            )
            return subscription_exists.exists()
        return False


class CustomUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('id', 'user', 'author')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True)
    ingredient = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'ingredient', 'name', 'measurement_unit', 'amount')

    def to_internal_value(self, data):
        ingredient_id = data.get('id')
        if ingredient_id:
            data['ingredient'] = ingredient_id
            data.pop('id', None)
        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'image', 'text', 'cooking_time',
                  'tags', 'ingredients', 'is_favorited', 'is_in_shopping_cart')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True).data
        return representation

    def to_internal_value(self, data):
        image = data.get('image')
        if image:
            data['image'] = decode_image(image, data.get('name'))
        return super().to_internal_value(data)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', [])
        tags_data = validated_data.pop('tags', [])

        recipe = Recipe.objects.create(author=self.context['request'].user,
                                       **validated_data)

        recipe_ingredients = []
        for data in ingredients_data:
            ingredient_id = data['ingredient'].id
            ingredient_obj = Ingredient.objects.get(id=ingredient_id)
            recipe_ingredient = RecipeIngredient(
                recipe=recipe, ingredient=ingredient_obj,
                amount=data['amount'])
            recipe_ingredients.append(recipe_ingredient)

        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        recipe.tags.set(tags_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', [])
        tags_data = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)

        if (ingredients_data
                and all('ingredient' in data for data in ingredients_data)):
            instance.recipe_ingredients.all().delete()

            recipe_ingredients = []
            for data in ingredients_data:
                ingredient_id = data['ingredient'].id
                ingredient_obj = Ingredient.objects.get(id=ingredient_id)
                recipe_ingredient = RecipeIngredient(
                    recipe=instance, ingredient=ingredient_obj,
                    amount=data['amount'])
                recipe_ingredients.append(recipe_ingredient)

            RecipeIngredient.objects.bulk_create(recipe_ingredients)
        instance.tags.set(tags_data)

        return instance

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return FavoriteRecipe.objects.filter(user=user,
                                                 recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return ShoppingList.objects.filter(user=user, recipe=obj).exists()
        return False


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteRecipe
        fields = ('id', 'user', 'recipe')


class ShoppingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = ('id', 'user', 'recipe')


class CustomUserWithRecipesSerializer(CustomUserSerializer):
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes',
                                                     'recipes_count')

    def get_recipes_count(self, obj):
        return obj.recipes.count()
