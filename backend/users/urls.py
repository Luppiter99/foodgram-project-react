from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'subscriptions', SubscriptionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
