from django.contrib import admin
from django.urls import include, path
from recipes.views import IngredientViewSet, RecipeViewSet, TagViewSet
from rest_framework.routers import DefaultRouter
from users.views import (CustomTokenObtainPairView, CustomUserViewSet,
                         SubscriptionViewSet, TokenDestroyView)

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'subscriptions', SubscriptionViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('api/auth/token/login/', CustomTokenObtainPairView.as_view(),
         name='custom_token_obtain_pair'),
    path('api/auth/token/logout/', TokenDestroyView.as_view(),
         name='token_destroy'),
]
