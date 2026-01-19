"""
Member Account Deletion URL Configuration
Path: /api/v1/members/delete-account/
"""
from django.urls import path
from users.views import member_delete_account_views

app_name = 'member_delete_account'

urlpatterns = [
    # Account deletion request page - GET: show form, POST: verify credentials
    # URL: /api/v1/members/delete-account/?tenant_id=xxx
    path('', 
         member_delete_account_views.MemberDeleteAccountRequestView.as_view(), 
         name='request'),
    
    # Confirmation page - POST: execute deletion
    # URL: /api/v1/members/delete-account/confirm/
    path('confirm/', 
         member_delete_account_views.MemberDeleteAccountConfirmView.as_view(), 
         name='confirm'),
    
    # Deletion complete page
    # URL: /api/v1/members/delete-account/complete/
    path('complete/', 
         member_delete_account_views.MemberDeleteAccountCompleteView.as_view(), 
         name='complete'),
]
