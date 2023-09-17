from rest_framework.pagination import PageNumberPagination


class CustomUserPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 1000
