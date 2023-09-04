from recipes.serializers import RecipeSerializer
from rest_framework import serializers

from .models import CustomUser, Subscription


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'date_of_birth', 'gender',
                  'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        subscription_exists = Subscription.objects.filter(
            user=self.context['request'].user,
            author=obj
        )
        return subscription_exists.exists()


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


class CustomUserWithRecipesSerializer(CustomUserSerializer):
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes',
                                                     'recipes_count')

    def get_recipes_count(self, obj):
        return obj.recipes.count()
