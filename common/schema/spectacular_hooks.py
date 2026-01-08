"""
DRF Spectacular 预处理钩子
用于为所有API路径添加安全要求和自定义标签
"""

def add_security_requirement(endpoints, **kwargs):
    """
    为所有API路径添加安全要求，确保每个API调用都需要JWT认证
    
    Args:
        endpoints: API端点列表
        kwargs: 其他参数
    
    Returns:
        处理后的API端点列表
    """
    # 为所有路径添加安全要求
    for (path, path_regex, method, callback) in endpoints:
        if hasattr(callback, 'kwargs') and 'public' in callback.kwargs and callback.kwargs['public']:
            # 如果endpoints明确标记为公开访问，则跳过
            continue
        
        # 检查路径是否已排除认证（如登录、注册等公共API）
        if path.startswith('/api/v1/auth/') or path == '/api/schema/' or path.startswith('/api/schema/'):
            continue
            
        # 为回调添加安全要求
        if not hasattr(callback, 'security'):
            callback.security = [{'Bearer': []}]
        elif not any('Bearer' in sec for sec in callback.security):
            callback.security.append({'Bearer': []})
    
    return endpoints


def customize_feedback_tags(result, generator, request, public):
    """
    自定义应用的标签，确保不同系统的端点使用正确的标签
    - feedbacks: 'Feedback System'
    - notifications (admin): '通知系统-管理端'
    - notifications (member): '通知系统-成员端'
    
    Args:
        result: OpenAPI schema 字典
        generator: Schema generator 实例
        request: HTTP 请求对象
        public: 是否为公共API
    
    Returns:
        修改后的 OpenAPI schema
    """
    if 'paths' not in result:
        return result
    
    # 遍历所有路径
    for path, path_item in result['paths'].items():
        # 检查路径是否属于 feedbacks 应用
        if '/feedbacks/' in path:
            # 遍历所有HTTP方法
            for method in ['get', 'post', 'put', 'patch', 'delete', 'options', 'head']:
                if method in path_item:
                    operation = path_item[method]
                    # 检查当前的 tags
                    current_tags = operation.get('tags', [])
                    
                    # 如果 tags 不是 ['Feedback System']，则替换
                    if current_tags != ['Feedback System']:
                        # 保留已经设置的 'Feedback System' tag，移除其他的
                        if 'Feedback System' in current_tags:
                            operation['tags'] = ['Feedback System']
                        # 如果当前是 'api' 或其他默认 tag，替换为 'Feedback System'
                        elif any(tag in ['api', 'feedbacks'] for tag in current_tags):
                            operation['tags'] = ['Feedback System']
        
        # 处理通知系统-管理端 (/api/v1/admin/notifications/)
        elif '/admin/notifications/' in path:
            for method in ['get', 'post', 'put', 'patch', 'delete', 'options', 'head']:
                if method in path_item:
                    operation = path_item[method]
                    current_tags = operation.get('tags', [])
                    
                    # 如果已经有正确的tag，保留；否则设置正确的tag
                    if '通知系统-管理端' in current_tags:
                        operation['tags'] = ['通知系统-管理端']
                    elif any(tag in ['api', 'admin', 'notifications'] for tag in current_tags):
                        operation['tags'] = ['通知系统-管理端']
        
        # 处理通知系统-成员端 (/api/v1/notifications/)
        elif '/notifications/' in path and '/admin/notifications/' not in path:
            for method in ['get', 'post', 'put', 'patch', 'delete', 'options', 'head']:
                if method in path_item:
                    operation = path_item[method]
                    current_tags = operation.get('tags', [])
                    
                    # 如果已经有正确的tag，保留；否则设置正确的tag
                    if '通知系统-成员端' in current_tags:
                        operation['tags'] = ['通知系统-成员端']
                    elif any(tag in ['api', 'notifications'] for tag in current_tags):
                        operation['tags'] = ['通知系统-成员端']
    
    return result
