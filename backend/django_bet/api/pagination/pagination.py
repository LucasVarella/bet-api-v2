# your_app/pagination/pagination.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response 

class CustomPageNumberPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response({
            'total_results': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'page': self.page.number,
            'page_size': self.page.paginator.per_page,
            'results': data
        })
