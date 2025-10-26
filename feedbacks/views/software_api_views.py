"""
Software Management APIViews
使用APIView模式，提供完全透明的权限检查和调试能力
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from ..models import SoftwareCategory, Software, SoftwareVersion
from ..serializers import (
    SoftwareCategorySerializer,
    SoftwareListSerializer,
    SoftwareDetailSerializer,
    SoftwareVersionSerializer
)
from ..permissions import is_tenant_admin


# ==================== Software Category APIs ====================

class SoftwareCategoryListView(APIView):
    """软件分类列表API - GET不需要认证"""
    permission_classes = [AllowAny]  # ✅ 所有GET API不需要认证
    
    @extend_schema(
        tags=['Feedback System'],
        summary='List software categories',
        description='Get a list of all software categories available in the system.',
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by active status'
            ),
        ],
        responses={200: SoftwareCategorySerializer(many=True)}
    )
    def get(self, request):
        """获取软件分类列表"""
        queryset = SoftwareCategory.objects.filter(is_deleted=False)
        
        if hasattr(request, 'tenant') and request.tenant:
            queryset = queryset.filter(tenant=request.tenant)
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ('true', '1'))
        
        queryset = queryset.order_by('sort_order', 'name')
        serializer = SoftwareCategorySerializer(queryset, many=True, context={'request': request})
        
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Create software category',
        description='Create a new software category. Only tenant administrators can perform this action.',
        request=SoftwareCategorySerializer,
        responses={201: SoftwareCategorySerializer, 403: OpenApiResponse(description='Permission denied')}
    )
    def post(self, request):
        """创建软件分类"""
        if not request.user or not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not is_tenant_admin(request.user):
            return Response({'detail': 'Only tenant administrators can create categories.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SoftwareCategorySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            category = serializer.save()
            if hasattr(request, 'tenant') and request.tenant:
                category.tenant = request.tenant
                category.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SoftwareCategoryDetailView(APIView):
    """软件分类详情API - GET不需要认证"""
    permission_classes = [AllowAny]  # ✅ 所有GET API不需要认证
    
    def get_object(self, pk, request):
        try:
            category = SoftwareCategory.objects.get(pk=pk, is_deleted=False)
            if hasattr(request, 'tenant') and request.tenant and category.tenant != request.tenant:
                return None
            return category
        except SoftwareCategory.DoesNotExist:
            return None
    
    @extend_schema(tags=['Feedback System'], summary='Get category details', responses={200: SoftwareCategorySerializer})
    def get(self, request, pk):
        category = self.get_object(pk, request)
        if not category:
            return Response({'detail': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SoftwareCategorySerializer(category, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(tags=['Feedback System'], summary='Update category', request=SoftwareCategorySerializer)
    def put(self, request, pk):
        return self._update(request, pk, partial=False)
    
    @extend_schema(tags=['Feedback System'], summary='Partially update category', request=SoftwareCategorySerializer)
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)
    
    def _update(self, request, pk, partial=False):
        if not is_tenant_admin(request.user):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        
        category = self.get_object(pk, request)
        if not category:
            return Response({'detail': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SoftwareCategorySerializer(category, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(tags=['Feedback System'], summary='Delete category')
    def delete(self, request, pk):
        if not is_tenant_admin(request.user):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        
        category = self.get_object(pk, request)
        if not category:
            return Response({'detail': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        category.is_deleted = True
        category.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==================== Software Product APIs ====================

class SoftwareListView(APIView):
    """软件产品列表API - GET不需要认证"""
    permission_classes = [AllowAny]  # ✅ 所有GET API不需要认证
    
    @extend_schema(
        tags=['Feedback System'],
        summary='List software products',
        parameters=[
            OpenApiParameter('category', OpenApiTypes.INT, OpenApiParameter.QUERY, description='Filter by category'),
            OpenApiParameter('status', OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter('is_active', OpenApiTypes.BOOL, OpenApiParameter.QUERY),
            OpenApiParameter('search', OpenApiTypes.STR, OpenApiParameter.QUERY),
        ],
        responses={200: SoftwareListSerializer(many=True)}
    )
    def get(self, request):
        queryset = Software.objects.filter(is_deleted=False)
        
        if hasattr(request, 'tenant') and request.tenant:
            queryset = queryset.filter(tenant=request.tenant)
        
        # Filters
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ('true', '1'))
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(code__icontains=search)
        
        queryset = queryset.order_by('name')
        serializer = SoftwareListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(tags=['Feedback System'], summary='Create software', request=SoftwareDetailSerializer)
    def post(self, request):
        if not is_tenant_admin(request.user):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SoftwareDetailSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            software = serializer.save()
            if hasattr(request, 'tenant') and request.tenant:
                software.tenant = request.tenant
                software.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SoftwareDetailView(APIView):
    """软件产品详情API - GET不需要认证"""
    permission_classes = [AllowAny]  # ✅ 所有GET API不需要认证
    
    def get_object(self, pk, request):
        try:
            software = Software.objects.get(pk=pk, is_deleted=False)
            if hasattr(request, 'tenant') and request.tenant and software.tenant != request.tenant:
                return None
            return software
        except Software.DoesNotExist:
            return None
    
    @extend_schema(tags=['Feedback System'], summary='Get software details', responses={200: SoftwareDetailSerializer})
    def get(self, request, pk):
        software = self.get_object(pk, request)
        if not software:
            return Response({'detail': 'Software not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SoftwareDetailSerializer(software, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(tags=['Feedback System'], summary='Update software', request=SoftwareDetailSerializer)
    def put(self, request, pk):
        return self._update(request, pk, partial=False)
    
    @extend_schema(tags=['Feedback System'], summary='Partially update software', request=SoftwareDetailSerializer)
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)
    
    def _update(self, request, pk, partial=False):
        if not is_tenant_admin(request.user):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        
        software = self.get_object(pk, request)
        if not software:
            return Response({'detail': 'Software not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SoftwareDetailSerializer(software, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(tags=['Feedback System'], summary='Delete software')
    def delete(self, request, pk):
        if not is_tenant_admin(request.user):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        
        software = self.get_object(pk, request)
        if not software:
            return Response({'detail': 'Software not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        software.is_deleted = True
        software.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SoftwareVersionsView(APIView):
    """软件版本管理API（嵌套在software下） - GET不需要认证"""
    permission_classes = [AllowAny]  # ✅ 所有GET API不需要认证
    
    @extend_schema(tags=['Feedback System'], summary='List software versions', responses={200: SoftwareVersionSerializer(many=True)})
    def get(self, request, software_pk):
        try:
            software = Software.objects.get(pk=software_pk, is_deleted=False)
            versions = software.versions.filter(is_deleted=False).order_by('-version_code')
            serializer = SoftwareVersionSerializer(versions, many=True, context={'request': request})
            return Response(serializer.data)
        except Software.DoesNotExist:
            return Response({'detail': 'Software not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(tags=['Feedback System'], summary='Add software version', request=SoftwareVersionSerializer)
    def post(self, request, software_pk):
        if not is_tenant_admin(request.user):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            software = Software.objects.get(pk=software_pk, is_deleted=False)
            
            # 准备数据：添加software字段，清理空字符串
            version_data = request.data.copy()
            version_data['software'] = software.id
            
            # 清理空字符串的可选字段
            if 'release_date' in version_data and version_data['release_date'] == '':
                version_data['release_date'] = None
            if 'download_url' in version_data and version_data['download_url'] == '':
                version_data['download_url'] = None
            if 'release_notes' in version_data and version_data['release_notes'] == '':
                version_data['release_notes'] = None
            
            serializer = SoftwareVersionSerializer(data=version_data, context={'request': request})
            if serializer.is_valid():
                version = serializer.save()
                if hasattr(request, 'tenant') and request.tenant:
                    version.tenant = request.tenant
                    version.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Software.DoesNotExist:
            return Response({'detail': 'Software not found.'}, status=status.HTTP_404_NOT_FOUND)


# ==================== Software Version APIs ====================

class SoftwareVersionListView(APIView):
    """软件版本列表API - GET不需要认证"""
    permission_classes = [AllowAny]  # ✅ 所有GET API不需要认证
    
    @extend_schema(
        tags=['Feedback System'],
        summary='List all software versions',
        parameters=[
            OpenApiParameter('software', OpenApiTypes.INT, OpenApiParameter.QUERY),
            OpenApiParameter('is_stable', OpenApiTypes.BOOL, OpenApiParameter.QUERY),
            OpenApiParameter('is_active', OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        ],
        responses={200: SoftwareVersionSerializer(many=True)}
    )
    def get(self, request):
        queryset = SoftwareVersion.objects.filter(is_deleted=False)
        
        if hasattr(request, 'tenant') and request.tenant:
            queryset = queryset.filter(tenant=request.tenant)
        
        software = request.query_params.get('software')
        if software:
            queryset = queryset.filter(software_id=software)
        
        is_stable = request.query_params.get('is_stable')
        if is_stable is not None:
            queryset = queryset.filter(is_stable=is_stable.lower() in ('true', '1'))
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ('true', '1'))
        
        queryset = queryset.order_by('-version_code')
        serializer = SoftwareVersionSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class SoftwareVersionDetailView(APIView):
    """软件版本详情API - GET不需要认证"""
    permission_classes = [AllowAny]  # ✅ 所有GET API不需要认证
    
    def get_object(self, pk, request):
        try:
            version = SoftwareVersion.objects.get(pk=pk, is_deleted=False)
            if hasattr(request, 'tenant') and request.tenant and version.tenant != request.tenant:
                return None
            return version
        except SoftwareVersion.DoesNotExist:
            return None
    
    @extend_schema(tags=['Feedback System'], summary='Get version details', responses={200: SoftwareVersionSerializer})
    def get(self, request, pk):
        version = self.get_object(pk, request)
        if not version:
            return Response({'detail': 'Version not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SoftwareVersionSerializer(version, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(tags=['Feedback System'], summary='Update version', request=SoftwareVersionSerializer)
    def put(self, request, pk):
        return self._update(request, pk, partial=False)
    
    @extend_schema(tags=['Feedback System'], summary='Partially update version', request=SoftwareVersionSerializer)
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)
    
    def _update(self, request, pk, partial=False):
        if not is_tenant_admin(request.user):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        
        version = self.get_object(pk, request)
        if not version:
            return Response({'detail': 'Version not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SoftwareVersionSerializer(version, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(tags=['Feedback System'], summary='Delete version')
    def delete(self, request, pk):
        if not is_tenant_admin(request.user):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        
        version = self.get_object(pk, request)
        if not version:
            return Response({'detail': 'Version not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        version.is_deleted = True
        version.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
