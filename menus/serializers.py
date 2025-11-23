"""
菜单管理系统序列化器
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Menu, UserMenu
from users.models import User


class MenuSerializer(serializers.ModelSerializer):
    """
    菜单序列化器
    """
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Menu.objects.all(),
        source='parent',
        allow_null=True,
        required=False
    )
    roles = serializers.ListField(child=serializers.CharField(allow_blank=True), required=False, allow_null=True, default=list)
    auths = serializers.ListField(child=serializers.CharField(allow_blank=True), required=False, allow_null=True, default=list)

    class Meta:
        model = Menu
        fields = [
            'id', 'name', 'code', 'path', 'component', 'redirect',
            'title', 'icon', 'extra_icon', 'rank', 'show_link', 'show_parent',
            'roles', 'auths', 'keep_alive', 'frame_src', 'frame_loading',
            'hidden_tag', 'dynamic_level', 'active_path',
            'transition_name', 'enter_transition', 'leave_transition',
            'parent_id', 'is_active', 'remarks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """
        验证菜单数据
        """
        # 检查是否存在循环引用
        instance = self.instance
        parent = data.get('parent')
        
        if instance and parent:
            if instance.id == parent.id:
                raise serializers.ValidationError({"parent_id": "Menu cannot set itself as parent menu"})
            
            # 检查父菜单是否是current菜单的子菜单
            descendants = instance.get_descendants()
            if parent in descendants:
                raise serializers.ValidationError({"parent_id": "Cannot set child menu as parent menu, this will cause circular reference"})
        
        return data


class MenuTreeSerializer(MenuSerializer):
    """
    菜单树形结构序列化器
    """
    children = serializers.SerializerMethodField()
    
    class Meta(MenuSerializer.Meta):
        fields = MenuSerializer.Meta.fields + ['children']
    
    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_children(self, obj):
        """
        获取子菜单
        """
        # 过滤非活跃菜单
        if self.context.get('is_active') is not None:
            is_active = self.context.get('is_active')
            children = obj.children.filter(is_active=is_active)
        else:
            children = obj.children.all()
            
        serializer = MenuTreeSerializer(children, many=True, context=self.context)
        return serializer.data


class UserMenuSerializer(serializers.ModelSerializer):
    """
    用户菜单关联序列化器
    """
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user'
    )
    menu_id = serializers.PrimaryKeyRelatedField(
        queryset=Menu.objects.all(),
        source='menu'
    )
    
    class Meta:
        model = UserMenu
        fields = ['id', 'user_id', 'menu_id', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserMenuDetailSerializer(serializers.ModelSerializer):
    """
    用户菜单详情序列化器
    """
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    menu_id = serializers.IntegerField(source='menu.id', read_only=True)
    menu_title = serializers.CharField(source='menu.title', read_only=True)
    menu_name = serializers.CharField(source='menu.name', read_only=True)
    menu_code = serializers.CharField(source='menu.code', read_only=True)
    
    class Meta:
        model = UserMenu
        fields = [
            'id', 'user_id', 'username', 'menu_id', 
            'menu_title', 'menu_name', 'menu_code', 'is_active', 
            'created_at', 'updated_at'
        ]


class UserMenusSerializer(serializers.Serializer):
    """
    用于批量分配菜单给用户的序列化器
    """
    menu_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        required=True
    )


class UserMenuSerializer(serializers.ModelSerializer):
    """
    用户菜单序列化器
    """
    class Meta:
        model = Menu
        fields = ['id', 'name', 'code', 'title', 'icon', 'path', 'component', 'rank']


# 定义一个递归字段，用于处理嵌套路由
class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


# 路由转场动画序列化器
class RouteTransitionSerializer(serializers.Serializer):
    """路由转场动画序列化器"""
    name = serializers.CharField(help_text="页面动画名称", required=False, allow_null=True)
    enterTransition = serializers.CharField(help_text="进场动画", required=False, allow_null=True)
    leaveTransition = serializers.CharField(help_text="离场动画", required=False, allow_null=True)


# 路由菜单序列化器
class RouteMetaSerializer(serializers.Serializer):
    """路由元数据序列化器"""
    title = serializers.CharField(help_text="菜单标题")
    icon = serializers.CharField(help_text="菜单图标", required=False, allow_null=True)
    extraIcon = serializers.CharField(help_text="额外图标", required=False, allow_null=True)
    rank = serializers.IntegerField(help_text="菜单排序", required=False, allow_null=True)
    roles = serializers.ListField(child=serializers.CharField(), help_text="可访问角色", required=False, allow_null=True)
    auths = serializers.ListField(child=serializers.CharField(), help_text="按钮级别权限", required=False, allow_null=True)
    showLink = serializers.BooleanField(help_text="是否在菜单中显示", required=False, default=True)
    showParent = serializers.BooleanField(help_text="是否显示父级菜单", required=False, default=True)
    keepAlive = serializers.BooleanField(help_text="是否缓存路由页面", required=False, default=False)
    frameSrc = serializers.CharField(help_text="iframe链接地址", required=False, allow_null=True)
    frameLoading = serializers.BooleanField(help_text="iframe是否开启首次加载动画", required=False, default=True)
    hiddenTag = serializers.BooleanField(help_text="禁止添加到标签页", required=False, default=False)
    dynamicLevel = serializers.IntegerField(help_text="标签页最大数量", required=False, allow_null=True)
    activePath = serializers.CharField(help_text="激活菜单的路径", required=False, allow_null=True)
    transition = RouteTransitionSerializer(help_text="页面加载动画", required=False, allow_null=True)


class RouteSerializer(serializers.Serializer):
    """路由序列化器"""
    path = serializers.CharField(help_text="路由路径")
    name = serializers.CharField(help_text="路由名称")
    component = serializers.CharField(help_text="组件路径", required=False, allow_null=True)
    redirect = serializers.CharField(help_text="重定向路径", required=False, allow_null=True)
    meta = RouteMetaSerializer(help_text="路由元数据")
    children = serializers.ListField(child=RecursiveField(), help_text="子路由", required=False)


class RoutesResponseSerializer(serializers.Serializer):
    """路由响应序列化器"""
    success = serializers.BooleanField(help_text="是否成功")
    code = serializers.IntegerField(help_text="状态码")
    message = serializers.CharField(help_text="消息")
    data = serializers.ListField(child=RouteSerializer(), help_text="路由数据") 