"""
User Feedback System Permissions

This module defines permission classes for controlling access to feedback system resources.
"""

from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


def is_tenant_admin(user):
    """
    Helper function to check if user is a tenant administrator (tenant_owner or app_admin).
    Super admins and regular users/members return False.
    """
    if not user or not user.is_authenticated:
        return False

    if not hasattr(user, 'is_admin'):
        return False

    return (
        user.is_admin and
        not getattr(user, 'is_super_admin', False) and
        not getattr(user, 'is_superuser', False)
    )


def is_tenant_owner_only(user):
    """
    Check if user is a tenant owner (excludes super_admin and app_admin).
    """
    return is_tenant_admin(user) and not getattr(user, 'is_app_admin', False)


def can_manage_feedback_app(user, application_id):
    """
    Check if tenant administrator can manage feedback resources for the given application_id.
    - tenant_owner: all applications in their tenant
    - app_admin: only applications returned by user.get_managed_app_ids()
    - super_admin / regular users: False
    """
    if not is_tenant_admin(user):
        return False

    if getattr(user, 'is_app_admin', False):
        if application_id is None:
            return False
        managed_app_ids = user.get_managed_app_ids() or []
        return application_id in managed_app_ids

    return True


def filter_feedback_queryset_for_user(queryset, user):
    """
    Scope Feedback queryset according to role:
    - super_admin: none (feedback management is restricted to tenant_owner and app_admin)
    - tenant_owner: all feedbacks in the tenant
    - app_admin: only feedbacks belonging to user.get_managed_app_ids()
    - regular authenticated user/member: only feedbacks submitted by user
    - anonymous: none
    """
    if not user or not user.is_authenticated:
        return queryset.none()

    if getattr(user, 'is_super_admin', False) or getattr(user, 'is_superuser', False):
        return queryset.none()

    if is_tenant_admin(user):
        if getattr(user, 'is_app_admin', False):
            managed_app_ids = user.get_managed_app_ids() or []
            return queryset.filter(application_id__in=managed_app_ids)
        return queryset

    return queryset.filter(user=user)


class IsTenantAdmin(permissions.BasePermission):
    """
    Permission check for tenant administrators.
    Only tenant admins can perform certain operations.
    """
    message = _("Only tenant administrators can perform this action.")
    
    def has_permission(self, request, view):
        """Check if user is a tenant admin"""
        return is_tenant_admin(request.user)


class SoftwareManagePermission(permissions.BasePermission):
    """
    Permission for managing software.
    - Only tenant admins can create, update, or delete software
    - Super admins CANNOT manage software
    - Everyone can view software
    """
    message = _("Only tenant administrators can manage software.")
    
    def has_permission(self, request, view):
        """Check permission at the view level"""
        # Anyone can view
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only authenticated users can proceed
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admins CANNOT manage software
        if request.user.is_superuser:
            self.message = _("Super administrators cannot manage software. This is restricted to tenant administrators.")
            return False
        
        # Only tenant admins can manage
        return is_tenant_admin(request.user)
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        # Anyone can view
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only authenticated users can proceed
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admins CANNOT manage software
        if request.user.is_superuser:
            return False
        
        # Only tenant admins of the same tenant can manage
        return (
            is_tenant_admin(request.user) and
            hasattr(request, 'tenant') and
            obj.tenant == request.tenant
        )


class FeedbackViewPermission(permissions.BasePermission):
    """
    Permission for viewing feedback.
    - Tenant owners can view all feedback from their tenant
    - Tenant app admins can view feedback for their managed applications
    - Regular users can only view their own feedback
    - Super admins and anonymous users cannot view feedback
    """
    message = _("You don't have permission to view this feedback.")
    
    def has_permission(self, request, view):
        """Check permission at the view level"""
        if not request.user or not request.user.is_authenticated:
            return False
        if getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'is_superuser', False):
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if hasattr(request, 'tenant') and obj.tenant != request.tenant:
            return False
        
        if can_manage_feedback_app(request.user, obj.application_id):
            return True
        
        if is_tenant_admin(request.user):
            return False
        
        return obj.user == request.user


class FeedbackCreatePermission(permissions.BasePermission):
    """
    Permission for creating feedback.
    - Anyone can create feedback (including anonymous users)
    """
    
    def has_permission(self, request, view):
        """Anyone can create feedback"""
        return True


class FeedbackUpdatePermission(permissions.BasePermission):
    """
    Permission for updating feedback.
    - Tenant owners and app admins (for managed apps) can update feedback in their tenant
    - Regular users can update their own feedback if it hasn't been replied to
    - Super admins and anonymous users cannot update feedback
    """
    message = _("You don't have permission to update this feedback.")
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        if not request.user or not request.user.is_authenticated:
            self.message = _("Anonymous users cannot update feedback.")
            return False
        
        if hasattr(request, 'tenant') and obj.tenant != request.tenant:
            return False
        
        if can_manage_feedback_app(request.user, obj.application_id):
            return True
        
        if is_tenant_admin(request.user):
            return False
        
        if obj.user == request.user:
            if obj.replies.filter(is_internal_note=False).exists():
                self.message = _("Cannot update feedback that has been replied to.")
                return False
            return True
        
        return False


class FeedbackDeletePermission(permissions.BasePermission):
    """
    Permission for deleting feedback.
    - Tenant owners and app admins (for managed apps) can delete feedback in their tenant
    - Regular users can delete their own feedback if it hasn't been replied to
    - Super admins and anonymous users cannot delete feedback
    """
    message = _("You don't have permission to delete this feedback.")
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        if not request.user or not request.user.is_authenticated:
            self.message = _("Anonymous users cannot delete feedback.")
            return False
        
        if hasattr(request, 'tenant') and obj.tenant != request.tenant:
            return False
        
        if can_manage_feedback_app(request.user, obj.application_id):
            return True
        
        if is_tenant_admin(request.user):
            return False
        
        if obj.user == request.user:
            if obj.replies.filter(is_internal_note=False).exists():
                self.message = _("Cannot delete feedback that has been replied to.")
                return False
            return True
        
        return False


class FeedbackReplyPermission(permissions.BasePermission):
    """
    Permission for replying to feedback.
    - Only tenant owners and app admins (for managed apps) can reply as administrators
    """
    message = _("Only tenant administrators can reply to feedback.")
    
    def has_permission(self, request, view):
        """Check permission at the view level"""
        return is_tenant_admin(request.user)
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        if hasattr(request, 'tenant') and obj.tenant != request.tenant:
            return False
        return can_manage_feedback_app(request.user, obj.application_id)


class FeedbackStatusChangePermission(permissions.BasePermission):
    """
    Permission for changing feedback status.
    - Only tenant owners and app admins (for managed apps) can change status
    """
    message = _("Only tenant administrators can change feedback status.")

    def has_permission(self, request, view):
        """Check permission at the view level"""
        return is_tenant_admin(request.user)
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        if hasattr(request, 'tenant') and obj.tenant != request.tenant:
            return False
        return can_manage_feedback_app(request.user, obj.application_id)


class FeedbackVotePermission(permissions.BasePermission):
    """
    Permission for voting on feedback.
    - Authenticated users can vote on feedback in their tenant
    - Anonymous users cannot vote
    """
    message = _("You must be logged in to vote on feedback.")
    
    def has_permission(self, request, view):
        """Check permission at the view level"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check tenant match (obj here is the feedback)
        if hasattr(request, 'tenant') and obj.tenant != request.tenant:
            self.message = _("You can only vote on feedback from your tenant.")
            return False
        
        return True


class StatisticsViewPermission(permissions.BasePermission):
    """
    Permission for viewing statistics.
    - Only tenant owners and app admins can view statistics
    - Statistics are limited to their own tenant (and managed apps for app_admin)
    """
    message = _("Only tenant administrators can view statistics.")
    
    def has_permission(self, request, view):
        """Check permission at the view level"""
        return is_tenant_admin(request.user)


class EmailTemplatePermission(permissions.BasePermission):
    """
    Permission for managing email templates.
    - Only tenant owners can manage tenant-wide email templates
    """
    message = _("Only tenant owners can manage email templates.")
    
    def has_permission(self, request, view):
        """Check permission at the view level"""
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return is_tenant_owner_only(request.user)
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return (
            is_tenant_owner_only(request.user) and
            hasattr(request, 'tenant') and
            obj.tenant == request.tenant
        )
