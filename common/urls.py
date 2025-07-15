"""
Common应用的URL配置
"""
from django.urls import path
from common import views
from common.views import (
    test_standard_response,
    test_error_response,
    test_auth_error_response,
    test_pagination_response,
    TestStandardResponseView,
    TestErrorResponseView,
    TestAuthErrorResponseView,
    TestPaginationResponseView,
    FileUploadView
)

app_name = 'common'

urlpatterns = [
    # API日志列表
    path('api-logs/', views.APILogListView.as_view(), name='api-log-list'),
    
    # API日志详情
    path('api-logs/<int:pk>/', views.APILogDetailView.as_view(), name='api-log-detail'),
    
    # 通用文件上传
    path('upload-file/', FileUploadView.as_view(), name='file-upload'),
    
    # 测试标准响应格式 - 类视图
    path('test-format-class/', TestStandardResponseView.as_view(), name='test-standard-response-class'),
    
    # 测试错误响应格式 - 类视图
    path('test-error-class/', TestErrorResponseView.as_view(), name='test-error-response-class'),
    
    # 测试认证失败响应格式 - 类视图
    path('test-auth-error-class/', TestAuthErrorResponseView.as_view(), name='test-auth-error-response-class'),
    
    # 测试分页响应格式 - 类视图
    path('test-pagination-class/', TestPaginationResponseView.as_view(), name='test-pagination-response-class'),
    
    # 保留原来的函数视图路由
    path('test-format/', test_standard_response, name='test-standard-response'),
    path('test-error/', test_error_response, name='test-error-response'),
    path('test-auth-error/', test_auth_error_response, name='test-auth-error-response'),
    path('test-pagination/', test_pagination_response, name='test-pagination-response'),
] 