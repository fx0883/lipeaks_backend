"""
视图集基类，提供多租户支持
"""
import logging
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

logger = logging.getLogger(__name__)

class TenantModelViewSet(viewsets.ModelViewSet):
    """
    多租户支持的模型视图集基类
    
    自动处理以下功能:
    1. 根据租户ID过滤查询集
    2. 创建对象时自动设置租户ID
    3. 验证对象所属租户与用户租户是否匹配
    
    权限控制规则：
    - GET请求允许匿名访问，但需要租户ID
    - 非GET请求需要认证，并且用户必须关联租户
    - 超级管理员可以通过X-Tenant-ID请求头指定租户进行操作
    - 只有URL路径中包含"cms"的API才需要进行租户ID验证
    """
    
    def get_queryset(self):
        """
        获取查询集并根据租户ID进行过滤
        
        支持两种租户过滤方式：
        1. 查询参数：?tenant_id=1
        2. 请求头：X-Tenant-ID: 1
        
        过滤逻辑：
        - 超级管理员：可以通过参数过滤特定租户，也可以看所有租户数据
        - 普通用户：只能看到自己租户的数据
        """
        queryset = super().get_queryset()
        
        # 记录视图集类名和请求路径
        view_name = self.__class__.__name__
        request_path = getattr(self.request, 'path', 'unknown_path')
        logger.info(f"[TenantModelViewSet] {view_name} 处理请求: {request_path}")
        
        # 检查请求路径是否包含"cms"，如果不包含，则跳过租户验证
        if "/cms/" not in self.request.path:
            logger.info(f"[TenantModelViewSet] {view_name} 非CMS路径，跳过租户过滤: {request_path}")
            return queryset
        
        # 获取租户信息
        tenant_id = getattr(self.request, 'tenant_id', None)
        tenant_source = getattr(self.request, 'tenant_source', None)
        is_super_admin_no_tenant = getattr(self.request, 'is_super_admin_no_tenant', False)
        
        logger.info(f"[TenantModelViewSet] {view_name} 获取到租户信息: tenant_id={tenant_id}, source={tenant_source}, is_super_admin_no_tenant={is_super_admin_no_tenant}")
        
        # 获取当前用户信息
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            is_super_admin = getattr(user, 'is_super_admin', False)
            user_tenant = getattr(user, 'tenant', None)
            logger.info(f"[TenantModelViewSet] {view_name} 用户: {user.username}, 超管: {is_super_admin}, 用户租户ID: {user_tenant.id if user_tenant else None}")
        else:
            logger.info(f"[TenantModelViewSet] {view_name} 用户未认证")
            is_super_admin = False
        
        # 如果模型没有tenant字段，则不需要过滤
        if not hasattr(queryset.model, 'tenant'):
            logger.info(f"[TenantModelViewSet] {view_name} 模型 {queryset.model.__name__} 没有tenant字段，跳过租户过滤")
            return queryset
        
        # 超级管理员特殊处理
        if is_super_admin:
            if tenant_source == 'query_param':
                # 查询参数指定的租户
                logger.info(f"[TenantModelViewSet] {view_name} 超级管理员通过查询参数过滤租户: {tenant_id}")
                return queryset.filter(tenant_id=tenant_id)
            elif tenant_source == 'header':
                # 请求头指定的租户
                logger.info(f"[TenantModelViewSet] {view_name} 超级管理员通过请求头过滤租户: {tenant_id}")
                return queryset.filter(tenant_id=tenant_id)
            elif is_super_admin_no_tenant:
                # 超级管理员没有指定租户，返回所有租户的数据
                logger.info(f"[TenantModelViewSet] {view_name} 超级管理员未指定租户，返回所有租户数据")
                return queryset
            else:
                # 其他情况，返回所有租户数据
                logger.info(f"[TenantModelViewSet] {view_name} 超级管理员返回所有租户数据")
                return queryset
        
        # 普通用户处理
        if tenant_id:
            # 有租户ID，按租户过滤
            logger.info(f"[TenantModelViewSet] {view_name} 普通用户按租户ID过滤: {tenant_id}")
            try:
                tenant_id = int(tenant_id)
                return queryset.filter(tenant_id=tenant_id)
            except (ValueError, TypeError):
                logger.error(f"[TenantModelViewSet] {view_name} 无效的租户ID: {tenant_id}")
                raise ValidationError({"detail": f"无效的租户ID: {tenant_id}"})
        else:
            # 没有租户ID，返回空查询集
            logger.warning(f"[TenantModelViewSet] {view_name} 普通用户未提供租户ID，返回空查询集")
            return queryset.none()
    
    def perform_create(self, serializer):
        """
        创建对象时自动设置租户ID
        """
        view_name = self.__class__.__name__
        
        # 检查请求路径是否包含"cms"，如果不包含，则跳过租户验证
        if "/cms/" not in self.request.path:
            logger.info(f"[TenantModelViewSet] {view_name} 非CMS路径，跳过租户设置: {self.request.path}")
            return serializer.save()
        
        # 获取当前租户ID
        tenant_id = getattr(self.request, 'tenant_id', None)
        logger.info(f"[TenantModelViewSet] {view_name} 创建对象时获取到租户ID: {tenant_id}")
        
        # 如果没有租户ID，则拒绝创建
        if not tenant_id:
            logger.warning(f"[TenantModelViewSet] {view_name} 尝试创建对象但未提供租户ID")
            raise ValidationError({"detail": "未提供租户ID，无法创建对象"})
        
        # 如果模型有tenant字段且有租户ID，则自动设置
        if tenant_id and hasattr(serializer.Meta.model, 'tenant'):
            model_name = serializer.Meta.model.__name__
            logger.info(f"[TenantModelViewSet] {view_name} 为模型 {model_name} 创建对象时设置租户ID: {tenant_id}")
            try:
                # 确保租户ID是整数
                tenant_id = int(tenant_id)
                
                # 超级管理员特殊处理：允许通过X-Tenant-ID请求头指定租户进行操作
                user = self.request.user
                is_super_admin = getattr(user, 'is_super_admin', False)
                
                if is_super_admin:
                    # 超级管理员已经在中间件中验证了租户ID的有效性
                    logger.info(f"[TenantModelViewSet] {view_name} 超级管理员 {user.username} 在租户 {tenant_id} 中创建对象")
                    serializer.save(tenant_id=tenant_id)
                    return
                
                # 验证普通用户是否关联该租户
                if user.is_authenticated and hasattr(user, 'tenant') and user.tenant:
                    user_tenant_id = str(user.tenant.id)
                    if user_tenant_id != str(tenant_id):
                        logger.warning(f"[TenantModelViewSet] {view_name} 用户 {user.username} 尝试在其他租户创建对象: 用户租户={user_tenant_id}, 请求租户={tenant_id}")
                        raise PermissionDenied("无法在其他租户创建对象")
                    
                    logger.info(f"[TenantModelViewSet] {view_name} 用户 {user.username} 在自己的租户 {tenant_id} 中创建对象")
                
                serializer.save(tenant_id=tenant_id)
            except (ValueError, TypeError):
                logger.error(f"[TenantModelViewSet] {view_name} 无效的租户ID: {tenant_id}")
                raise ValidationError({"detail": f"无效的租户ID: {tenant_id}"})
        else:
            # 如果没有租户ID但模型需要，则拒绝创建
            if hasattr(serializer.Meta.model, 'tenant') and \
               serializer.Meta.model._meta.get_field('tenant').null is False:
                logger.warning(f"[TenantModelViewSet] {view_name} 尝试创建对象但未提供租户ID")
                raise PermissionDenied("无法创建对象: 未提供租户ID")
            
            serializer.save()
    
    def perform_update(self, serializer):
        """
        更新对象时验证租户ID不变
        """
        view_name = self.__class__.__name__
        
        # 检查请求路径是否包含"cms"，如果不包含，则跳过租户验证
        if "/cms/" not in self.request.path:
            logger.info(f"[TenantModelViewSet] {view_name} 非CMS路径，跳过租户验证: {self.request.path}")
            return serializer.save()
        
        # 获取当前对象
        instance = serializer.instance
        logger.info(f"[TenantModelViewSet] {view_name} 更新对象: {instance.__class__.__name__} ID={instance.pk}")
        
        # 验证对象所属租户
        self._verify_tenant_ownership(instance)
        
        # 执行更新
        logger.info(f"[TenantModelViewSet] {view_name} 租户验证通过，执行更新操作")
        serializer.save()
    
    def perform_destroy(self, instance):
        """
        删除对象前验证租户ID
        """
        view_name = self.__class__.__name__
        
        # 检查请求路径是否包含"cms"，如果不包含，则跳过租户验证
        if "/cms/" not in self.request.path:
            logger.info(f"[TenantModelViewSet] {view_name} 非CMS路径，跳过租户验证: {self.request.path}")
            return instance.delete()
        
        # 验证对象所属租户
        logger.info(f"[TenantModelViewSet] {view_name} 删除对象: {instance.__class__.__name__} ID={instance.pk}")
        self._verify_tenant_ownership(instance)
        
        # 执行删除
        logger.info(f"[TenantModelViewSet] {view_name} 租户验证通过，执行删除操作")
        instance.delete()
    
    def _verify_tenant_ownership(self, obj):
        """
        验证对象所属租户与当前租户ID是否匹配
        
        Args:
            obj: 要验证的对象
            
        Raises:
            PermissionDenied: 如果对象不属于当前租户
        """
        view_name = self.__class__.__name__
        
        # 检查请求路径是否包含"cms"，如果不包含，则跳过租户验证
        if "/cms/" not in self.request.path:
            logger.info(f"[TenantModelViewSet] {view_name} 非CMS路径，跳过租户验证: {self.request.path}")
            return
        
        # 如果对象没有tenant字段，则跳过验证
        if not hasattr(obj, 'tenant'):
            logger.info(f"[TenantModelViewSet] {view_name} 对象 {obj.__class__.__name__} 没有tenant字段，跳过租户验证")
            return
            
        # 获取当前租户ID
        tenant_id = getattr(self.request, 'tenant_id', None)
        
        # 如果没有设置租户ID，则拒绝访问
        if not tenant_id:
            logger.warning(f"[TenantModelViewSet] {view_name} 尝试操作对象但未提供租户ID")
            raise PermissionDenied("无法操作对象: 未提供租户ID")
            
        # 验证对象所属租户与当前租户ID是否匹配
        obj_tenant_id = str(obj.tenant.id) if obj.tenant else None
        logger.info(f"[TenantModelViewSet] {view_name} 验证租户所有权: 对象租户ID={obj_tenant_id}, 当前租户ID={tenant_id}")
        
        if obj_tenant_id and obj_tenant_id != str(tenant_id):
            logger.warning(f"[TenantModelViewSet] {view_name} 尝试操作不属于当前租户的对象: 对象租户ID={obj_tenant_id}, 当前租户ID={tenant_id}")
            raise PermissionDenied("无法操作不属于当前租户的对象") 