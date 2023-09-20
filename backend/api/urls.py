from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    CustomTokenObtainPairView,
    TokenLogoutConfirmationView
)

router_v1 = DefaultRouter()
router_v1.register(r'users', CustomUserViewSet)
router_v1.register(r'recipes', RecipeViewSet)
router_v1.register(r'tags', TagViewSet)
router_v1.register(r'ingredients', IngredientViewSet)

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/token/login/', CustomTokenObtainPairView.as_view(),
         name='custom_token_obtain_pair'),
    path('auth/token/logout/', TokenLogoutConfirmationView.as_view(),
         name='token_logout'),
]
