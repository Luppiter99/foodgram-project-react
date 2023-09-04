from django.db import models
from users.models import CustomUser


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    measurement_unit = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                               related_name='recipes')
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='recipes/')
    text = models.TextField()
    cooking_time = models.PositiveIntegerField()
    tags = models.ManyToManyField(Tag, through='RecipeTag')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient')

    def __str__(self):
        return self.name


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(CustomUser, related_name='favorite_recipes',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='favorited_by',
                               on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} likes {self.recipe.name}"


class ShoppingList(models.Model):
    user = models.ForeignKey(CustomUser, related_name='shopping_lists',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='in_shopping_list',
                               on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.recipe.name} is in {self.user.username}'s shopping list"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='ingredient_recipes')
    amount = models.PositiveIntegerField()

    def __str__(self):
        return (
            f"{self.amount} {self.ingredient.measurement_unit} "
            f"of {self.ingredient.name} in {self.recipe.name}"
        )


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,
                            related_name='tag_recipes')

    def __str__(self):
        return f"{self.tag.name} for {self.recipe.name}"
