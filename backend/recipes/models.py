from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from users.models import CustomUser
from .utils import validate_color


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, unique=True,
                             validators=[validate_color])
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    measurement_unit = models.CharField(max_length=50)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique_ingredient')
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                               related_name='recipes', blank=True)

    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='recipes/')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name="Date of Publication")
    text = models.TextField()
    cooking_time = models.PositiveIntegerField(validators=[
        MinValueValidator(1),
        MaxValueValidator(1440)
    ])

    tags = models.ManyToManyField(Tag, through='RecipeTag')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient')

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_user_recipe')
        ]
        ordering = ['user_id']

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class FavoriteRecipe(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_favorite_recipe')
        ]


class ShoppingList(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_shopping_list')
        ]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='ingredient_recipes')
    amount = models.PositiveIntegerField(validators=[
        MinValueValidator(1),
        MaxValueValidator(10000)
    ])

    class Meta:
        ordering = ['recipe_id']
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'],
                                    name='unique_recipe_ingredient')
        ]

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

    class Meta:
        ordering = ['recipe_id']
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'tag'],
                                    name='unique_recipe_tag')
        ]

    def __str__(self):
        return f"{self.tag.name} for {self.recipe.name}"
