"""
分页相关模块
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PaginatedDict(dict):
    """
    兼具字典与列表特性的分页容器字典。
    在提供 pagination 与 results 标准字典键的同时，支持整数下标访问与基于结果集数量的 len()，
    实现对旧式单测 (如 items = response.data['data']; len(items); items[0]) 的平滑向后兼容。
    """
    def __init__(self, data_dict, items):
        super().__init__(data_dict)
        self.items_list = items

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.items_list[key]
        return super().__getitem__(key)

    def __len__(self):
        return len(self.items_list)

    def __iter__(self):
        return iter(self.items_list)


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
            'page_size': self.page.paginator.per_page,
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
        }
        
        paginated_dict = PaginatedDict({
            'pagination': pagination_info,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        }, data)
        
        return Response(paginated_dict)
