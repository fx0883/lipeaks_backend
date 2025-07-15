"""
分页相关模块
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    标准分页类，自定义响应格式
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        自定义分页响应格式
        
        Args:
            data: 分页后的数据
        
        Returns:
            自定义格式的Response对象
        """
        pagination_info = {
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page_size': self.page_size,
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
        }
        
        # 此处不需要包装为标准格式，因为StandardJSONRenderer会处理
        # 我们只需将分页信息与结果数据组合成合适的结构
        return Response({
            'pagination': pagination_info,
            'results': data
        }) 