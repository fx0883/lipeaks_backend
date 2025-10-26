"""
User Feedback System Permissions

This module defines permission classes for controlling access to feedback system resources.
"""

from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


def is_tenant_admin(user):
    """
    Helper function to check if user is a tenant administrator
    
    Args:
        user: User object
        
    Returns:
        bool: True if user is a tenant admin, False otherwise
    """
    # User must be authenticated
    if not user or not user.is_authenticated:
        return False
    
    # Check if this is a User model instance (not Member)
    # User has is_admin field, Member doesn't
    if not hasattr(user, 'is_admin'):
        return False
    
    # Must be admin but not super admin
    return (
        user.is_admin and 
        not getattr(user, 'is_super_admin', False)
    )


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
    - Super admins can only view feedback from their tenant
    - Tenant admins can view all feedback from their tenant
    - Regular users can only view their own feedback
    - Anonymous users cannot view any feedback
    """
    message = _("You don't have permission to view this feedback.")
    
    def has_permission(self, request, view):
        """Check permission at the view level"""
        # Must be authenticated to view feedback list
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check tenant match first
        if hasattr(request, 'tenant') and obj.tenant != request.tenant:
            return False
        
        # Super admin can view all feedback in their tenant
        if request.user.is_superuser:
            return True
        
        # Tenant admin can view all feedback in their tenant
        if is_tenant_admin(request.user):
            return True
        
        # Regular users can only view their own feedback
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
    - Super admins and tenant admins can update any feedback in their tenant
    - Regular users can update their own feedback if it hasn't been replied to
    - Anonymous users cannot update feedback
    """
    message = _("You don't have permission to update this feedback.")
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        if not request.user or not request.user.is_authenticated:
            self.message = _("Anonymous users cannot update feedback.")
            return False
        
        # Check tenant match
        if hasattr(request, 'tenant') and obj.tenant != request.tenant:
            return False
        
        # Super admin and tenant admin can update
        if request.user.is_superuser:
            return True
        
        if is_tenant_admin(request.user):
            return True
        
        # Regular users can update their own feedback if not replied
        if obj.user == request.user:
            if obj.replies.filter(is_internal_note=False).exists():
                self.message = _("Cannot update feedback that has been replied to.")
                return False
            return True
        
        return False


class FeedbackDeletePermission(permissions.BasePermission):
    """
    Permission for deleting feedback.
    - Super admins and tenant admins can delete any feedback in their tenant
    - Regular users can delete their own feedback if it hasn't been replied to
    - Anonymous users cannot delete feedback
    """
    message = _("You don't have permission to delete this feedback.")
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        if not request.user or not request.user.is_authenticated:
            self.message = _("Anonymous users cannot delete feedback.")
            return False
        
        # Check tenant match
        if hasattr(request, 'tenant') and obj.tenant != request.tenant:
            return False
        
        # Super admin and tenant admin can delete
        if request.user.is_superuser:
            return True
        
        if is_tenant_admin(request.user):
            return True
        
        # Regular users can delete their own feedback if not replied
        if obj.user == request.user:
            if obj.replies.filter(is_internal_note=False).exists():
                self.message = _("Cannot delete feedback that has been replied to.")
                return False
            return True
        
        return False


class FeedbackReplyPermission(permissions.BasePermission):
    """
    Permission for replying to feedback.
    - Only super admins and tenant admins can reply to feedback
    - Regular users and anonymous users cannot reply
    """
    message = _("Only administrators can reply to feedback.")
    
    def has_permission(self, request, view):
        """Check permission at the view level"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Only admins can reply
        return (
            request.user.is_superuser or
            is_tenant_admin(request.user)
        )
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check tenant match (obj here is the feedback)
        if hasattr(request, 'tenant') and obj.tenant != request.tenant:
            return False
        
        # Only admins can reply
        return (
            request.user.is_superuser or
            is_tenant_admin(request.user)
        )


class FeedbackStatusChangePermission(permissions.BasePermission):
    """
    Permission for changing feedback status.
    - Only super admins and tenant admins can change status
    """
    message = _("Only administrators can change feedback status.")
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check tenant match
        if hasattr(request, 'tenant') and obj.tenant != request.tenant:
            return False
        
        # Only admins can change status
        return (
            request.user.is_superuser or
            is_tenant_admin(request.user)
        )


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
    - Only super admins and tenant admins can view statistics
    - Statistics are limited to their own tenant
    """
    message = _("Only administrators can view statistics.")
    
    def has_permission(self, request, view):
        """Check permission at the view level"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Only admins can view statistics
        return (
            request.user.is_superuser or
            is_tenant_admin(request.user)
        )


class EmailTemplatePermission(permissions.BasePermission):
    """
    Permission for managing email templates.
    - Only tenant admins can manage email templates
    - Super admins can view but not edit
    """
    message = _("Only tenant administrators can manage email templates.")
    
    def has_permission(self, request, view):
        """Check permission at the view level"""
        # Anyone authenticated can view
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Only tenant admins can manage
        if not request.user or not request.user.is_authenticated:
            return False
        
        return (
            is_tenant_admin(request.user)
        )
    
    def has_object_permission(self, request, view, obj):
        """Check permission at the object level"""
        # Anyone authenticated can view
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Only tenant admins of the same tenant can manage
        if not request.user or not request.user.is_authenticated:
            return False
        
        return (
            is_tenant_admin(request.user) and
            hasattr(request, 'tenant') and
            obj.tenant == request.tenant
        )
