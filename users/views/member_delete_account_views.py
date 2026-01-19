"""
Member Account Deletion Views (Server-side pages)
Provides HTML form-based account deletion flow for Google Play Data Safety compliance

URL: /api/v1/members/delete-account/
Required parameter: tenant_id (URL parameter)
Language: English only
"""
import logging
import secrets
import string
from django.views.generic import FormView, TemplateView
from django.urls import reverse
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.hashers import check_password

from users.forms_delete_account import AccountDeletionLoginForm, AccountDeletionConfirmForm
from users.models import Member
from tenants.models import Tenant

logger = logging.getLogger(__name__)


def get_manager(model_class):
    """Get manager that bypasses soft delete filter"""
    if hasattr(model_class, 'original_objects'):
        return model_class.original_objects
    return model_class.objects


class MemberDeleteAccountRequestView(FormView):
    """
    Member account deletion request page view
    GET: Display login form
    POST: Verify credentials, redirect to confirmation page
    Required URL parameter: ?tenant_id=xxx
    """
    template_name = 'members/account_delete_request.html'
    form_class = AccountDeletionLoginForm
    
    def dispatch(self, request, *args, **kwargs):
        """Validate required URL parameters"""
        self.tenant_id = request.GET.get('tenant_id')
        self.tenant = None
        
        # Validate tenant_id is present
        if not self.tenant_id:
            return render(request, 'members/account_delete_error.html', {
                'error_message': 'Invalid access. Please use the correct link with tenant_id parameter.'
            })
        
        # Validate tenant exists and is active
        try:
            self.tenant = Tenant.objects.get(id=self.tenant_id, status='active', is_deleted=False)
        except (Tenant.DoesNotExist, ValueError):
            return render(request, 'members/account_delete_error.html', {
                'error_message': 'Application not found or inactive.'
            })
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """Pass URL parameter tenant_id to form"""
        kwargs = super().get_form_kwargs()
        kwargs['initial_tenant_id'] = self.tenant_id
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Add tenant info to context"""
        context = super().get_context_data(**kwargs)
        context['tenant'] = self.tenant
        context['tenant_id'] = self.tenant_id
        return context
    
    def form_valid(self, form):
        """Handle valid form submission - verify credentials"""
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        tenant_id = int(form.cleaned_data['tenant_id'])
        
        # Find member by username or email
        member = Member.objects.filter(
            tenant_id=tenant_id,
            is_active=True,
            is_deleted=False,
            status='active',
            parent__isnull=True  # Exclude sub-accounts
        ).filter(
            # Match by username or email
            **({'username': username} if '@' not in username else {'email': username})
        ).first()
        
        # If not found by exact match, try the other field
        if not member and '@' in username:
            member = Member.objects.filter(
                email=username,
                tenant_id=tenant_id,
                is_active=True,
                is_deleted=False,
                status='active',
                parent__isnull=True
            ).first()
        elif not member:
            member = Member.objects.filter(
                username=username,
                tenant_id=tenant_id,
                is_active=True,
                is_deleted=False,
                status='active',
                parent__isnull=True
            ).first()
        
        if not member:
            messages.error(self.request, 'Invalid username/email or password.')
            return self.form_invalid(form)
        
        # Verify password
        if not member.check_password(password):
            messages.error(self.request, 'Invalid username/email or password.')
            logger.warning(f"Account deletion: invalid password for member {username} (tenant:{tenant_id})")
            return self.form_invalid(form)
        
        # Generate a temporary token for the confirmation step
        token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        # Store in session for verification
        self.request.session['delete_account_member_id'] = member.id
        self.request.session['delete_account_token'] = token
        self.request.session['delete_account_tenant_id'] = tenant_id
        self.request.session.set_expiry(600)  # 10 minutes
        
        logger.info(f"Account deletion: credentials verified for member {member.username} (tenant:{tenant_id})")
        
        # Redirect to confirmation page
        return render(self.request, 'members/account_delete_confirm.html', {
            'member': member,
            'tenant': self.tenant,
            'tenant_id': self.tenant_id,
            'token': token,
            'data_types': self.get_data_types_summary(member)
        })
    
    def get_data_types_summary(self, member):
        """Get summary of data types that will be deleted"""
        data_types = []
        
        # Check each data type
        data_types.append({
            'name': 'Account Information',
            'description': 'Username, email, profile details, avatar'
        })
        
        # WeChat binding
        try:
            from wechat.models import WechatUser
            count = get_manager(WechatUser).filter(member=member).count()
            if count > 0:
                data_types.append({
                    'name': 'WeChat Binding',
                    'description': f'{count} linked account(s)'
                })
        except:
            pass
        
        # Check-in system
        try:
            from check_system.models import CheckRecord, Task, CheckinCycle
            records = get_manager(CheckRecord).filter(member=member).count()
            tasks = get_manager(Task).filter(member=member).count()
            cycles = get_manager(CheckinCycle).filter(member=member).count()
            if records + tasks + cycles > 0:
                data_types.append({
                    'name': 'Check-in Data',
                    'description': f'{records} records, {tasks} tasks, {cycles} cycles'
                })
        except:
            pass
        
        # CMS content
        try:
            from cms.models import Article, Comment
            articles = get_manager(Article).filter(member=member).count()
            comments = get_manager(Comment).filter(member=member).count()
            if articles + comments > 0:
                data_types.append({
                    'name': 'Content',
                    'description': f'{articles} articles, {comments} comments'
                })
        except:
            pass
        
        # Interactions
        try:
            from interactions.models import MemberLike, MemberFollow, ArticleLike
            likes = get_manager(ArticleLike).filter(member=member).count()
            member_likes = get_manager(MemberLike).filter(member=member).count()
            follows = get_manager(MemberFollow).filter(member=member).count()
            if likes + member_likes + follows > 0:
                data_types.append({
                    'name': 'Social Interactions',
                    'description': f'{likes + member_likes} likes, {follows} follows'
                })
        except:
            pass
        
        # Notifications
        try:
            from notifications.models import NotificationRecipient
            count = get_manager(NotificationRecipient).filter(member=member).count()
            if count > 0:
                data_types.append({
                    'name': 'Notifications',
                    'description': f'{count} notification(s)'
                })
        except:
            pass
        
        # Points
        try:
            from points.models import TenantUserProfile, TenantUserPoints
            profiles = get_manager(TenantUserProfile).filter(member=member).count()
            points = get_manager(TenantUserPoints).filter(member=member).count()
            if profiles + points > 0:
                data_types.append({
                    'name': 'Points & Profile',
                    'description': 'Loyalty points and profile data'
                })
        except:
            pass
        
        return data_types


class MemberDeleteAccountConfirmView(FormView):
    """
    Member account deletion confirmation page view
    POST: Execute account deletion
    """
    template_name = 'members/account_delete_confirm.html'
    form_class = AccountDeletionConfirmForm
    
    def dispatch(self, request, *args, **kwargs):
        """Validate session data"""
        self.member_id = request.session.get('delete_account_member_id')
        self.token = request.session.get('delete_account_token')
        self.tenant_id = request.session.get('delete_account_tenant_id')
        
        if not all([self.member_id, self.token, self.tenant_id]):
            return render(request, 'members/account_delete_error.html', {
                'error_message': 'Session expired. Please start the deletion process again.'
            })
        
        # Get member
        try:
            self.member = Member.objects.get(id=self.member_id, is_deleted=False)
            self.tenant = Tenant.objects.get(id=self.tenant_id, status='active', is_deleted=False)
        except (Member.DoesNotExist, Tenant.DoesNotExist):
            return render(request, 'members/account_delete_error.html', {
                'error_message': 'Account not found or already deleted.'
            })
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Handle deletion confirmation"""
        form_token = request.POST.get('token')
        confirm_delete = request.POST.get('confirm_delete')
        
        # Verify token
        if form_token != self.token:
            return render(request, 'members/account_delete_error.html', {
                'error_message': 'Invalid verification token. Please start the deletion process again.'
            })
        
        # Verify checkbox
        if not confirm_delete:
            messages.error(request, 'You must confirm that you understand the deletion is permanent.')
            return render(request, 'members/account_delete_confirm.html', {
                'member': self.member,
                'tenant': self.tenant,
                'tenant_id': self.tenant_id,
                'token': self.token,
                'data_types': MemberDeleteAccountRequestView.get_data_types_summary(None, self.member)
            })
        
        # Execute deletion
        try:
            deleted_data = self.delete_member_data(self.member)
            
            # Clear session
            for key in ['delete_account_member_id', 'delete_account_token', 'delete_account_tenant_id']:
                if key in request.session:
                    del request.session[key]
            
            logger.info(f"Account deletion completed for member {self.member.username} (id:{self.member.id}, tenant:{self.tenant_id})")
            
            return render(request, 'members/account_delete_complete.html', {
                'tenant': self.tenant,
                'deleted_data': deleted_data
            })
            
        except Exception as e:
            logger.error(f"Account deletion failed for member {self.member.id}: {str(e)}")
            return render(request, 'members/account_delete_error.html', {
                'error_message': 'An error occurred while deleting your account. Please try again or contact support.'
            })
    
    @transaction.atomic
    def delete_member_data(self, member):
        """Delete all member data - follows hard_delete_all_members.py pattern"""
        deleted_data = []
        
        # 1. Delete WeChat bindings
        try:
            from wechat.models import WechatUser
            count = get_manager(WechatUser).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'WeChat bindings: {count}')
        except Exception as e:
            logger.warning(f"Error deleting WechatUser for member {member.id}: {e}")
        
        # 2. Delete check-in system data
        try:
            from check_system.models import CheckRecord, Task, CheckinCycle
            
            count = get_manager(CheckRecord).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Check-in records: {count}')
            
            count = get_manager(Task).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Tasks: {count}')
            
            count = get_manager(CheckinCycle).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Check-in cycles: {count}')
        except Exception as e:
            logger.warning(f"Error deleting check_system data for member {member.id}: {e}")
        
        # 3. Delete CMS data
        try:
            from cms.models import Article, Comment, OperationLog
            
            count = get_manager(Comment).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Comments: {count}')
            
            count = get_manager(OperationLog).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Operation logs: {count}')
            
            count = get_manager(Article).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Articles: {count}')
        except Exception as e:
            logger.warning(f"Error deleting cms data for member {member.id}: {e}")
        
        # 4. Delete interactions
        try:
            from interactions.models import MemberLike, MemberFollow, ArticleLike
            
            count = get_manager(ArticleLike).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Article likes: {count}')
            
            count = get_manager(MemberLike).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Member likes: {count}')
            
            count = get_manager(MemberFollow).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Follows: {count}')
        except Exception as e:
            logger.warning(f"Error deleting interactions for member {member.id}: {e}")
        
        # 5. Delete notifications
        try:
            from notifications.models import NotificationRecipient
            count = get_manager(NotificationRecipient).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Notifications: {count}')
        except Exception as e:
            logger.warning(f"Error deleting notifications for member {member.id}: {e}")
        
        # 6. Delete licenses
        try:
            from licenses.models import LicenseAssignment
            count = get_manager(LicenseAssignment).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'License assignments: {count}')
        except Exception as e:
            logger.warning(f"Error deleting licenses for member {member.id}: {e}")
        
        # 7. Delete customer relations
        try:
            from customers.models import CustomerMemberRelation
            count = get_manager(CustomerMemberRelation).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Customer relations: {count}')
        except Exception as e:
            logger.warning(f"Error deleting customer relations for member {member.id}: {e}")
        
        # 8. Delete points data
        try:
            from points.models import TenantUserProfile, TenantUserPoints, TenantUserTypeTag
            
            count = get_manager(TenantUserTypeTag).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'User tags: {count}')
            
            count = get_manager(TenantUserPoints).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Points records: {count}')
            
            count = get_manager(TenantUserProfile).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'User profiles: {count}')
        except Exception as e:
            logger.warning(f"Error deleting points data for member {member.id}: {e}")
        
        # 9. Delete password reset tokens
        try:
            from users.models import PasswordResetToken
            count = get_manager(PasswordResetToken).filter(member=member).delete()[0]
            if count > 0:
                deleted_data.append(f'Password reset tokens: {count}')
        except Exception as e:
            logger.warning(f"Error deleting password reset tokens for member {member.id}: {e}")
        
        # 10. Delete sub-accounts first
        try:
            sub_accounts = Member.objects.filter(parent=member)
            count = sub_accounts.count()
            if count > 0:
                sub_accounts.delete()
                deleted_data.append(f'Sub-accounts: {count}')
        except Exception as e:
            logger.warning(f"Error deleting sub-accounts for member {member.id}: {e}")
        
        # 11. Finally delete the member
        username = member.username
        member.delete()
        deleted_data.append(f'Account: {username}')
        
        return deleted_data


class MemberDeleteAccountCompleteView(TemplateView):
    """Account deletion complete page - for direct access only"""
    template_name = 'members/account_delete_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['deleted_data'] = []
        return context
