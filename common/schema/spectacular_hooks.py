"""
DRF Spectacular 预处理钩子
用于为所有API路径添加安全要求
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
