from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    CustomTokenObtainPairView,
    TokenDestroyView
)

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', CustomTokenObtainPairView.as_view(),
         name='custom_token_obtain_pair'),
    path('auth/token/logout/', TokenDestroyView.as_view(),
         name='token_destroy'),
]
