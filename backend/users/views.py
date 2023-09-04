from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, Subscription
from .serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                          CustomUserWithRecipesSerializer,
                          SubscriptionSerializer)


class CustomUserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 1000


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = CustomUserSerializer
    pagination_class = CustomUserPagination

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = CustomUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_data = CustomUserCreateSerializer(user).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response({'field_name': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        user = self.request.user
        author = self.get_object()

        if user.id == author.id:
            return Response({'error': 'Cannot subscribe to yourself'},
                            status=status.HTTP_400_BAD_REQUEST)

        Subscription.objects.get_or_create(user=user, author=author)
        return Response({'message': 'Successfully subscribed'},
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['DELETE'],
            permission_classes=[IsAuthenticated])
    def unsubscribe(self, request, pk=None):
        user = self.request.user
        author = self.get_object()

        subscription = Subscription.objects.filter(user=user, author=author)
        if not subscription.exists():
            return Response({'error': 'Not subscribed'},
                            status=status.HTTP_400_BAD_REQUEST)

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['POST'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({'error': 'Missing required fields'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({'error': 'Invalid current password'},
                            status=status.HTTP_401_UNAUTHORIZED)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password successfully changed'},
                        status=status.HTTP_204_NO_CONTENT)


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all().order_by('id')
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        subscriptions = Subscription.objects.filter(
            user=request.user
        ).prefetch_related('author')

        subscriptions = subscriptions.prefetch_related('author__recipes')

        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = CustomUserWithRecipesSerializer(
                [sub.author for sub in page],
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = CustomUserWithRecipesSerializer(
            [sub.author for sub in subscriptions],
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email', None)
        password = request.data.get('password', None)

        if not email or not password:
            return Response({'detail': 'Email and password are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = get_user_model().objects.filter(email=email).first()

        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'auth_token': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)

        return Response({
            'error': 'Invalid credentials',
        }, status=status.HTTP_401_UNAUTHORIZED)


class TokenDestroyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            request.auth.blacklist()
        except AttributeError:
            return Response({'detail': 'Invalid token'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)
