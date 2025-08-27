"""
视图集基类，提供多租户支持
"""
import logging
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.conf import settings
from common.utils.tenant_header import get_header_tenant_id, require_member_header_match
from common.exceptions import TenantHeaderInvalidOrMissing, TenantMismatchOrNoPermission

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
        
        # 如果模型没有tenant字段，则不需要过滤
        if not hasattr(queryset.model, 'tenant'):
            logger.info(f"[TenantModelViewSet] {view_name} 模型 {queryset.model.__name__} 没有tenant字段，跳过租户过滤")
            return queryset
        
        # feature flag：开启后按新规则执行租户来源与角色分流
        if getattr(settings, 'FEATURE_ENFORCE_TENANT_HEADER_FOR_MEMBER', True):
            request = self.request
            user = getattr(request, 'user', None)
            is_auth = bool(user and getattr(user, 'is_authenticated', False))
            is_super_admin = bool(is_auth and getattr(request, 'auth_type', None) == 'jwt' and getattr(user, 'is_super_admin', False))
            is_tenant_admin = bool(is_auth and getattr(user, 'is_admin', False) and not is_super_admin)

            # 防御性：管理员/超管禁头（应被中间件拦截，这里再次保障）
            header_tid = get_header_tenant_id(request)
            if (is_super_admin or is_tenant_admin) and header_tid is not None:
                logger.warning(f"[TenantModelViewSet] {view_name} 管理员/超管携带X-Tenant-ID被拒绝")
                raise TenantHeaderInvalidOrMissing()

            # 计算有效租户ID
            effective_tenant_id = None
            if is_super_admin:
                q_tid = request.GET.get('tenant_id')
                if q_tid is not None:
                    try:
                        effective_tenant_id = int(q_tid)
                    except (TypeError, ValueError):
                        raise TenantHeaderInvalidOrMissing()
                else:
                    # GET可以不指定 -> 返回全量；非GET在写操作里另行校验
                    logger.info(f"[TenantModelViewSet] {view_name} 超管未提供tenant_id参数，GET场景返回全量")
                    return queryset
            elif is_tenant_admin:
                q_tid = request.GET.get('tenant_id')
                if q_tid is not None:
                    try:
                        effective_tenant_id = int(q_tid)
                    except (TypeError, ValueError):
                        raise TenantHeaderInvalidOrMissing()
                else:
                    user_tenant = getattr(user, 'tenant', None)
                    if user_tenant:
                        effective_tenant_id = int(user_tenant.id)
                    else:
                        # 管理员无绑定租户视为无权限
                        raise TenantMismatchOrNoPermission()
            else:
                # 成员或匿名：仅用Header并校验匹配
                require_member_header_match(request)
                # 再取到已验证的header作为过滤租户
                header_tid_val = get_header_tenant_id(request)
                if header_tid_val is None:
                    raise TenantHeaderInvalidOrMissing()
                effective_tenant_id = int(header_tid_val)

            logger.info(f"[TenantModelViewSet] {view_name} 按新规则过滤租户: {effective_tenant_id}")
            return queryset.filter(tenant_id=effective_tenant_id)
        
        # feature flag 关闭：维持旧逻辑（依赖中间件注入的 request.tenant_id 等）
        tenant_id = getattr(self.request, 'tenant_id', None)
        tenant_source = getattr(self.request, 'tenant_source', None)
        is_super_admin_no_tenant = getattr(self.request, 'is_super_admin_no_tenant', False)
        logger.info(f"[TenantModelViewSet] {view_name} 获取到租户信息: tenant_id={tenant_id}, source={tenant_source}, is_super_admin_no_tenant={is_super_admin_no_tenant}")
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            is_super_admin = getattr(user, 'is_super_admin', False)
            user_tenant = getattr(user, 'tenant', None)
            logger.info(f"[TenantModelViewSet] {view_name} 用户: {user.username}, 超管: {is_super_admin}, 用户租户ID: {user_tenant.id if user_tenant else None}")
        else:
            logger.info(f"[TenantModelViewSet] {view_name} 用户未认证")
            is_super_admin = False
        if is_super_admin:
            if tenant_source == 'query_param':
                logger.info(f"[TenantModelViewSet] {view_name} 超级管理员通过查询参数过滤租户: {tenant_id}")
                return queryset.filter(tenant_id=tenant_id)
            elif tenant_source == 'header':
                logger.info(f"[TenantModelViewSet] {view_name} 超级管理员通过请求头过滤租户: {tenant_id}")
                return queryset.filter(tenant_id=tenant_id)
            elif is_super_admin_no_tenant:
                logger.info(f"[TenantModelViewSet] {view_name} 超级管理员未指定租户，返回所有租户数据")
                return queryset
            else:
                logger.info(f"[TenantModelViewSet] {view_name} 超级管理员返回所有租户数据")
                return queryset
        if tenant_id:
            logger.info(f"[TenantModelViewSet] {view_name} 普通用户按租户ID过滤: {tenant_id}")
            try:
                tenant_id = int(tenant_id)
                return queryset.filter(tenant_id=tenant_id)
            except (ValueError, TypeError):
                logger.error(f"[TenantModelViewSet] {view_name} 无效的租户ID: {tenant_id}")
                raise ValidationError({"detail": f"无效的租户ID: {tenant_id}"})
        else:
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
        
        # 计算有效租户ID（新规则下覆盖 request.tenant_id）
        tenant_id = self._effective_tenant_id_for_write()
        logger.info(f"[TenantModelViewSet] {view_name} 创建对象使用有效租户ID: {tenant_id}")
        
        # 如果模型有tenant字段且有租户ID，则自动设置
        if tenant_id and hasattr(serializer.Meta.model, 'tenant'):
            model_name = serializer.Meta.model.__name__
            logger.info(f"[TenantModelViewSet] {view_name} 为模型 {model_name} 创建对象时设置租户ID: {tenant_id}")
            try:
                # 确保租户ID是整数
                tenant_id = int(tenant_id)
                
                # 有效租户ID基于角色已校验匹配/权限
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
        if tenant_id is None:
            logger.warning(f"[TenantModelViewSet] {view_name} 尝试操作对象但未提供租户ID")
            raise PermissionDenied("无法操作对象: 未提供租户ID")
            
        # 验证对象所属租户与当前租户ID是否匹配
        obj_tenant_id = str(obj.tenant.id) if obj.tenant else None
        logger.info(f"[TenantModelViewSet] {view_name} 验证租户所有权: 对象租户ID={obj_tenant_id}, 当前租户ID={tenant_id}")
        
        if obj_tenant_id and obj_tenant_id != str(tenant_id):
            logger.warning(f"[TenantModelViewSet] {view_name} 尝试操作不属于当前租户的对象: 对象租户ID={obj_tenant_id}, 当前租户ID={tenant_id}")
            raise PermissionDenied("无法操作不属于当前租户的对象") 

    # —— 辅助方法：按新规则计算有效租户 ——
    def _effective_tenant_id_for_read(self, default_none_ok: bool = False):
        """为读取场景确定有效租户ID。仅在CMS路径使用。"""
        if "/cms/" not in self.request.path:
            return None
        if not getattr(settings, 'FEATURE_ENFORCE_TENANT_HEADER_FOR_MEMBER', True):
            return getattr(self.request, 'tenant_id', None)

        request = self.request
        user = getattr(request, 'user', None)
        is_auth = bool(user and getattr(user, 'is_authenticated', False))
        is_super_admin = bool(is_auth and getattr(request, 'auth_type', None) == 'jwt' and getattr(user, 'is_super_admin', False))
        is_tenant_admin = bool(is_auth and getattr(user, 'is_admin', False) and not is_super_admin)

        header_tid = get_header_tenant_id(request)
        if (is_super_admin or is_tenant_admin) and header_tid is not None:
            raise TenantHeaderInvalidOrMissing()

        if is_super_admin:
            q_tid = request.GET.get('tenant_id')
            if q_tid is not None:
                try:
                    return int(q_tid)
                except (TypeError, ValueError):
                    raise TenantHeaderInvalidOrMissing()
            return None if default_none_ok else None
        if is_tenant_admin:
            q_tid = request.GET.get('tenant_id')
            if q_tid is not None:
                try:
                    return int(q_tid)
                except (TypeError, ValueError):
                    raise TenantHeaderInvalidOrMissing()
            user_tenant = getattr(user, 'tenant', None)
            if user_tenant:
                return int(user_tenant.id)
            raise TenantMismatchOrNoPermission()

        # 成员/匿名
        require_member_header_match(request)
        tid = get_header_tenant_id(request)
        if tid is None:
            raise TenantHeaderInvalidOrMissing()
        return int(tid)

    def _effective_tenant_id_for_write(self):
        """为写操作确定有效租户ID，严格规则。"""
        if "/cms/" not in self.request.path:
            return getattr(self.request, 'tenant_id', None)
        request = self.request
        if not getattr(settings, 'FEATURE_ENFORCE_TENANT_HEADER_FOR_MEMBER', True):
            tid = getattr(request, 'tenant_id', None)
            if tid is None:
                raise ValidationError({"detail": "未提供租户ID，无法创建对象"})
            return tid

        user = getattr(request, 'user', None)
        is_auth = bool(user and getattr(user, 'is_authenticated', False))
        is_super_admin = bool(is_auth and getattr(request, 'auth_type', None) == 'jwt' and getattr(user, 'is_super_admin', False))
        is_tenant_admin = bool(is_auth and getattr(user, 'is_admin', False) and not is_super_admin)

        header_tid = get_header_tenant_id(request)
        if (is_super_admin or is_tenant_admin) and header_tid is not None:
            raise TenantHeaderInvalidOrMissing()

        if is_super_admin:
            q_tid = request.GET.get('tenant_id')
            if q_tid is None:
                # 确认：超管写操作必须提供?tenant_id=
                raise TenantHeaderInvalidOrMissing()
            try:
                return int(q_tid)
            except (TypeError, ValueError):
                raise TenantHeaderInvalidOrMissing()
        if is_tenant_admin:
            q_tid = request.GET.get('tenant_id')
            if q_tid is not None:
                try:
                    return int(q_tid)
                except (TypeError, ValueError):
                    raise TenantHeaderInvalidOrMissing()
            user_tenant = getattr(user, 'tenant', None)
            if user_tenant:
                return int(user_tenant.id)
            raise TenantMismatchOrNoPermission()

        # 成员/匿名
        require_member_header_match(request)
        tid = get_header_tenant_id(request)
        if tid is None:
            raise TenantHeaderInvalidOrMissing()
        return int(tid)

    # —— 为成员/匿名 CMS GET 添加 Vary: X-Tenant-ID ——
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        try:
            if request and request.method == 'GET' and '/cms/' in getattr(request, 'path', ''):
                user = getattr(request, 'user', None)
                is_auth = bool(user and getattr(user, 'is_authenticated', False))
                is_super_admin = bool(is_auth and getattr(request, 'auth_type', None) == 'jwt' and getattr(user, 'is_super_admin', False))
                is_tenant_admin = bool(is_auth and getattr(user, 'is_admin', False) and not is_super_admin)
                # 仅对成员/匿名添加Vary
                if not (is_super_admin or is_tenant_admin):
                    vary = response.headers.get('Vary') or response.get('Vary')
                    header_name = 'X-Tenant-ID'
                    if vary:
                        if header_name not in str(vary):
                            response['Vary'] = f"{vary}, {header_name}"
                    else:
                        response['Vary'] = header_name
        except Exception:
            # 响应对象可能因渲染器差异不具备headers属性，尽量容错
            pass
        return response