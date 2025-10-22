"""
Software Management Views

This module contains views for managing software categories, software products, and versions.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse
)
from drf_spectacular.types import OpenApiTypes
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..models import SoftwareCategory, Software, SoftwareVersion
from ..serializers import (
    SoftwareCategorySerializer,
    SoftwareListSerializer,
    SoftwareDetailSerializer,
    SoftwareVersionSerializer
)
from ..permissions import SoftwareManagePermission


@extend_schema_view(
    list=extend_schema(
        tags=['Software Management'],
        summary='List software categories',
        description='Get a list of all software categories available in the system.',
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by active status'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in name and description'
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=SoftwareCategorySerializer(many=True),
                description='List of software categories',
                examples=[
                    OpenApiExample(
                        'Success Response',
                        value=[
                            {
                                'id': 1,
                                'name': 'Web Applications',
                                'code': 'web',
                                'description': 'Web-based software applications',
                                'icon': 'web',
                                'sort_order': 1,
                                'is_active': True,
                                'software_count': 5,
                                'created_at': '2025-01-01T00:00:00Z',
                                'updated_at': '2025-01-01T00:00:00Z'
                            }
                        ]
                    )
                ]
            )
        }
    ),
    create=extend_schema(
        tags=['Software Management'],
        summary='Create software category',
        description='Create a new software category. Only tenant administrators can perform this action.',
        request=SoftwareCategorySerializer,
        responses={
            201: OpenApiResponse(
                response=SoftwareCategorySerializer,
                description='Category created successfully'
            ),
            400: OpenApiResponse(description='Invalid input data'),
            403: OpenApiResponse(description='Permission denied')
        },
        examples=[
            OpenApiExample(
                'Create Category Request',
                value={
                    'name': 'Mobile Applications',
                    'code': 'mobile',
                    'description': 'Mobile software applications',
                    'icon': 'smartphone',
                    'sort_order': 2,
                    'is_active': True
                },
                request_only=True
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['Software Management'],
        summary='Get software category details',
        description='Retrieve detailed information about a specific software category.',
        responses={
            200: SoftwareCategorySerializer,
            404: OpenApiResponse(description='Category not found')
        }
    ),
    update=extend_schema(
        tags=['Software Management'],
        summary='Update software category',
        description='Update all fields of a software category. Only tenant administrators can perform this action.',
        request=SoftwareCategorySerializer,
        responses={
            200: SoftwareCategorySerializer,
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Category not found')
        }
    ),
    partial_update=extend_schema(
        tags=['Software Management'],
        summary='Partially update software category',
        description='Update specific fields of a software category. Only tenant administrators can perform this action.',
        request=SoftwareCategorySerializer,
        responses={
            200: SoftwareCategorySerializer,
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Category not found')
        }
    ),
    destroy=extend_schema(
        tags=['Software Management'],
        summary='Delete software category',
        description='Soft delete a software category. Only tenant administrators can perform this action.',
        responses={
            204: OpenApiResponse(description='Category deleted successfully'),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Category not found')
        }
    )
)
class SoftwareCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing software categories"""
    queryset = SoftwareCategory.objects.filter(is_deleted=False)
    serializer_class = SoftwareCategorySerializer
    permission_classes = [SoftwareManagePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description', 'code']
    ordering_fields = ['sort_order', 'name', 'created_at']
    ordering = ['sort_order', 'name']


@extend_schema_view(
    list=extend_schema(
        tags=['Software Management'],
        summary='List software products',
        description='Get a list of all software products in the system.',
        parameters=[
            OpenApiParameter(
                name='category',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by category ID'
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by status (development, testing, released, maintenance, deprecated)',
                enum=['development', 'testing', 'released', 'maintenance', 'deprecated']
            ),
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by active status'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in name, code, and description'
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=SoftwareListSerializer(many=True),
                description='List of software products',
                examples=[
                    OpenApiExample(
                        'Success Response',
                        value=[
                            {
                                'id': 1,
                                'name': 'CRM System',
                                'code': 'crm_system',
                                'description': 'Customer Relationship Management System',
                                'category': 1,
                                'category_name': 'Web Applications',
                                'logo': 'http://example.com/logo.png',
                                'current_version': 'v2.1.0',
                                'status': 'released',
                                'is_active': True,
                                'total_feedbacks': 42,
                                'open_feedbacks': 5,
                                'version_count': 10,
                                'created_at': '2025-01-01T00:00:00Z',
                                'updated_at': '2025-01-01T00:00:00Z'
                            }
                        ]
                    )
                ]
            )
        }
    ),
    create=extend_schema(
        tags=['Software Management'],
        summary='Create software product',
        description='Create a new software product. Only tenant administrators can perform this action.',
        request=SoftwareDetailSerializer,
        responses={
            201: OpenApiResponse(
                response=SoftwareDetailSerializer,
                description='Software created successfully'
            ),
            400: OpenApiResponse(description='Invalid input data'),
            403: OpenApiResponse(description='Permission denied')
        },
        examples=[
            OpenApiExample(
                'Create Software Request',
                value={
                    'name': 'ERP System',
                    'code': 'erp_system',
                    'description': 'Enterprise Resource Planning System',
                    'category_id': 1,
                    'website': 'https://erp.example.com',
                    'owner': 'John Doe',
                    'team': 'ERP Team',
                    'contact_email': 'support@erp.example.com',
                    'tags': ['enterprise', 'saas', 'cloud'],
                    'status': 'released',
                    'is_active': True
                },
                request_only=True
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['Software Management'],
        summary='Get software product details',
        description='Retrieve detailed information about a specific software product, including versions.',
        responses={
            200: SoftwareDetailSerializer,
            404: OpenApiResponse(description='Software not found')
        }
    ),
    update=extend_schema(
        tags=['Software Management'],
        summary='Update software product',
        description='Update all fields of a software product. Only tenant administrators can perform this action.',
        request=SoftwareDetailSerializer,
        responses={
            200: SoftwareDetailSerializer,
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Software not found')
        }
    ),
    partial_update=extend_schema(
        tags=['Software Management'],
        summary='Partially update software product',
        description='Update specific fields of a software product. Only tenant administrators can perform this action.',
        request=SoftwareDetailSerializer,
        responses={
            200: SoftwareDetailSerializer,
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Software not found')
        }
    ),
    destroy=extend_schema(
        tags=['Software Management'],
        summary='Delete software product',
        description='Soft delete a software product. Only tenant administrators can perform this action.',
        responses={
            204: OpenApiResponse(description='Software deleted successfully'),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Software not found')
        }
    )
)
class SoftwareViewSet(viewsets.ModelViewSet):
    """ViewSet for managing software products"""
    queryset = Software.objects.filter(is_deleted=False)
    permission_classes = [SoftwareManagePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'status', 'is_active']
    search_fields = ['name', 'code', 'description', 'tags']
    ordering_fields = ['name', 'created_at', 'total_feedbacks', 'open_feedbacks']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'list':
            return SoftwareListSerializer
        return SoftwareDetailSerializer
    
    @extend_schema(
        tags=['Software Management'],
        summary='Add version to software',
        description='Add a new version to a software product. Only tenant administrators can perform this action.',
        request=SoftwareVersionSerializer,
        responses={
            201: OpenApiResponse(
                response=SoftwareVersionSerializer,
                description='Version added successfully'
            ),
            400: OpenApiResponse(description='Invalid input data'),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Software not found')
        },
        examples=[
            OpenApiExample(
                'Add Version Request',
                value={
                    'version': 'v2.2.0',
                    'version_code': 220,
                    'release_date': '2025-01-15',
                    'release_notes': 'New features and bug fixes',
                    'is_stable': True,
                    'is_active': True,
                    'download_url': 'https://example.com/download/v2.2.0'
                },
                request_only=True
            )
        ]
    )
    @action(detail=True, methods=['post'], url_path='versions')
    def add_version(self, request, pk=None):
        """Add a new version to the software"""
        software = self.get_object()
        serializer = SoftwareVersionSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(software=software, tenant=request.tenant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Software Management'],
        summary='List software versions',
        description='Get all versions of a software product.',
        responses={
            200: OpenApiResponse(
                response=SoftwareVersionSerializer(many=True),
                description='List of software versions'
            ),
            404: OpenApiResponse(description='Software not found')
        }
    )
    @action(detail=True, methods=['get'], url_path='versions')
    def list_versions(self, request, pk=None):
        """List all versions of the software"""
        software = self.get_object()
        versions = software.versions.filter(is_deleted=False).order_by('-version_code')
        serializer = SoftwareVersionSerializer(versions, many=True, context={'request': request})
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=['Software Management'],
        summary='List all software versions',
        description='Get a list of all software versions across all products.',
        parameters=[
            OpenApiParameter(
                name='software',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by software ID'
            ),
            OpenApiParameter(
                name='is_stable',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by stable status'
            ),
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by active status'
            ),
        ],
        responses={
            200: SoftwareVersionSerializer(many=True)
        }
    ),
    retrieve=extend_schema(
        tags=['Software Management'],
        summary='Get version details',
        description='Retrieve details of a specific software version.',
        responses={
            200: SoftwareVersionSerializer,
            404: OpenApiResponse(description='Version not found')
        }
    ),
    update=extend_schema(
        tags=['Software Management'],
        summary='Update software version',
        description='Update a software version. Only tenant administrators can perform this action.',
        request=SoftwareVersionSerializer,
        responses={
            200: SoftwareVersionSerializer,
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Version not found')
        }
    ),
    partial_update=extend_schema(
        tags=['Software Management'],
        summary='Partially update software version',
        description='Update specific fields of a software version. Only tenant administrators can perform this action.',
        request=SoftwareVersionSerializer,
        responses={
            200: SoftwareVersionSerializer,
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Version not found')
        }
    ),
    destroy=extend_schema(
        tags=['Software Management'],
        summary='Delete software version',
        description='Soft delete a software version. Only tenant administrators can perform this action.',
        responses={
            204: OpenApiResponse(description='Version deleted successfully'),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Version not found')
        }
    )
)
class SoftwareVersionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing software versions"""
    queryset = SoftwareVersion.objects.filter(is_deleted=False)
    serializer_class = SoftwareVersionSerializer
    permission_classes = [SoftwareManagePermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['software', 'is_stable', 'is_active']
    ordering_fields = ['version_code', 'release_date', 'created_at']
    ordering = ['-version_code']
