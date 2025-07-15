"""
菜单路由视图
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from common.models import Config
from ..models import Menu, UserMenu
from ..serializers import RoutesResponseSerializer

logger = logging.getLogger(__name__)


def build_route_from_menu(menu):
    """
    从菜单对象构建路由配置
    
    Args:
        menu: 菜单对象
        
    Returns:
        dict: 路由配置字典
    """
    # 构建元数据
    meta = {
        'title': menu.title,
        'rank': menu.rank,
        'showLink': menu.show_link
    }
    
    # 添加非空字段
    if menu.icon:
        meta['icon'] = menu.icon
    if menu.extra_icon:
        meta['extraIcon'] = menu.extra_icon
    if menu.show_parent is not None:
        meta['showParent'] = menu.show_parent
    if menu.roles:
        meta['roles'] = menu.roles
    if menu.auths:
        meta['auths'] = menu.auths
    if menu.keep_alive is not None:
        meta['keepAlive'] = menu.keep_alive
    if menu.frame_src:
        meta['frameSrc'] = menu.frame_src
    if menu.frame_loading is not None:
        meta['frameLoading'] = menu.frame_loading
    if menu.hidden_tag is not None:
        meta['hiddenTag'] = menu.hidden_tag
    if menu.dynamic_level is not None:
        meta['dynamicLevel'] = menu.dynamic_level
    if menu.active_path:
        meta['activePath'] = menu.active_path
        
    # 处理转场动画
    if menu.transition_name or menu.enter_transition or menu.leave_transition:
        transition = {}
        if menu.transition_name:
            transition['name'] = menu.transition_name
        if menu.enter_transition:
            transition['enterTransition'] = menu.enter_transition
        if menu.leave_transition:
            transition['leaveTransition'] = menu.leave_transition
        meta['transition'] = transition
    
    # 构建路由对象
    route = {
        'path': menu.path,
        'name': menu.name,
        'meta': meta
    }
    
    # 添加非空字段
    if menu.component:
        route['component'] = menu.component
    if menu.redirect:
        route['redirect'] = menu.redirect
        
    # 处理子菜单
    children = Menu.objects.filter(parent=menu, is_active=True).order_by('rank')
    if children:
        route['children'] = [build_route_from_menu(child) for child in children]
        
    return route


class AdminRoutesView(APIView):
    """
    管理员菜单路由API
    提供前端路由配置，支持超级管理员和租户管理员
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: RoutesResponseSerializer()},
        description="获取管理员菜单路由",
        summary="获取管理员菜单路由",
        tags=["菜单"]
    )
    def get(self, request):
        """
        获取管理员菜单路由
        根据用户角色返回相应的菜单路由配置
        """
        user = request.user
        
        # 判断用户是否为超级管理员
        if user.is_super_admin:
            try:
                # 从配置中获取超级管理员菜单
                config = Config.objects.get(key='super_admin_menu', is_active=True)
                routes = config.value
                
                return Response({
                    'success': True,
                    'code': 2000,
                    'message': '获取路由成功',
                    'data': routes
                })
            except Config.DoesNotExist:
                # 配置不存在，尝试从菜单模型构建
                try:
                    # 获取顶级菜单
                    top_menus = Menu.objects.filter(
                        is_active=True, 
                        parent__isnull=True
                    ).order_by('rank')
                    
                    if top_menus:
                        # 构建路由配置
                        routes = [build_route_from_menu(menu) for menu in top_menus]
                        
                        return Response({
                            'success': True,
                            'code': 2000,
                            'message': '获取路由成功',
                            'data': routes
                        })
                    else:
                        logger.warning("系统中没有定义菜单")
                except Exception as e:
                    logger.error(f"构建菜单路由失败: {str(e)}")
                
                # 如果构建失败，返回错误
                logger.error("超级管理员菜单配置不存在")
                return Response({
                    'success': False,
                    'code': 4004,
                    'message': '菜单配置不存在',
                    'data': []
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # 处理租户管理员菜单
            if user.tenant and user.is_tenant_admin:
                try:
                    # 从用户菜单中获取配置
                    user_menu_ids = UserMenu.objects.filter(
                        user=user, 
                        is_active=True
                    ).values_list('menu_id', flat=True)
                    
                    if user_menu_ids:
                        # 获取顶级菜单项
                        top_menus = Menu.objects.filter(
                            id__in=user_menu_ids, 
                            is_active=True, 
                            parent__isnull=True
                        ).order_by('rank')
                        
                        # 构建路由配置
                        routes = [build_route_from_menu(menu) for menu in top_menus]
                        
                        return Response({
                            'success': True,
                            'code': 2000,
                            'message': '获取路由成功',
                            'data': routes
                        })
                    else:
                        logger.warning(f"用户 {user.username} 没有分配菜单")
                except Exception as e:
                    logger.error(f"获取用户菜单失败: {str(e)}")
            
            # 如果不是租户管理员或处理失败，返回空数组
            return Response({
                'success': True,
                'code': 2000,
                'message': '获取路由成功',
                'data': []
            }) 