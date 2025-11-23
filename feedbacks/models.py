"""
User Feedback System Models

This module contains all data models for the feedback management system,
including software management, feedback tracking, and email management.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from common.models import BaseModel
import uuid
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


# ===================== Software Management Models =====================
# Software/SoftwareCategory/SoftwareVersion已移至applications模块
# 现在使用 applications.Application 和 applications.ApplicationVersion


# ===================== Feedback Management Models =====================

class Feedback(BaseModel):
    """
    User Feedback Model
    Core model for storing user feedback submissions
    """
    TYPE_CHOICES = [
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('improvement', 'Improvement'),
        ('question', 'Question'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('reviewing', 'Reviewing'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
        ('duplicate', 'Duplicate'),
    ]
    
    PRIORITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    # Submission Information
    title = models.CharField(
        _("Title"), 
        max_length=200, 
        help_text="Brief description of the issue"
    )
    description = models.TextField(
        _("Description"), 
        help_text="Detailed description"
    )
    feedback_type = models.CharField(
        _("Feedback Type"), 
        max_length=20, 
        choices=TYPE_CHOICES, 
        default='bug', 
        db_index=True
    )
    priority = models.CharField(
        _("Priority"), 
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default='medium', 
        db_index=True
    )
    status = models.CharField(
        _("Status"), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='submitted', 
        db_index=True
    )
    
    # Application Association
    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name=_("Related Application"),
        db_index=True,
        null=True,
        blank=True
    )
    
    # Submitter Information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='submitted_feedbacks',
        verbose_name=_("User"),
        blank=True,
        null=True,
        help_text="Registered user (if logged in)"
    )
    contact_email = models.EmailField(
        _("Contact Email"), 
        blank=True,
        null=True,
        help_text="Email for replies (required for anonymous users)"
    )
    contact_name = models.CharField(
        _("Contact Name"), 
        max_length=100, 
        blank=True, 
        null=True
    )
    
    # Email Notification Settings
    email_verified = models.BooleanField(
        _("Email Verified"), 
        default=False
    )
    email_verification_token = models.CharField(
        _("Email Verification Token"), 
        max_length=100, 
        blank=True, 
        null=True
    )
    email_verification_sent_at = models.DateTimeField(
        _("Verification Email Sent At"), 
        blank=True, 
        null=True
    )
    email_notification_enabled = models.BooleanField(
        _("Email Notifications Enabled"), 
        default=True
    )
    
    # Environment Information
    environment_info = models.JSONField(
        _("Environment Information"), 
        default=dict, 
        blank=True, 
        help_text="OS, browser, hardware and other environment info"
    )
    
    # Tracking Information
    ip_address = models.GenericIPAddressField(
        _("IP Address"), 
        blank=True, 
        null=True
    )
    user_agent = models.CharField(
        _("User Agent"), 
        max_length=500, 
        blank=True, 
        null=True
    )
    
    # Processing Information
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_feedbacks',
        verbose_name=_("Assigned To"),
        blank=True,
        null=True
    )
    resolved_at = models.DateTimeField(
        _("Resolved At"), 
        blank=True, 
        null=True
    )
    resolution_notes = models.TextField(
        _("Resolution Notes"), 
        blank=True, 
        null=True
    )
    
    # Statistics
    view_count = models.PositiveIntegerField(
        _("View Count"), 
        default=0
    )
    vote_count = models.IntegerField(
        _("Vote Count"), 
        default=0
    )
    reply_count = models.PositiveIntegerField(
        _("Reply Count"), 
        default=0
    )
    
    class Meta:
        db_table = 'feedback_feedback'
        verbose_name = _('Feedback')
        verbose_name_plural = _('Feedbacks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'feedback_type']),
            models.Index(fields=['tenant', 'priority']),
            models.Index(fields=['application', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['contact_email']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"[{self.get_feedback_type_display()}] {self.title}"
    
    def save(self, *args, **kwargs):
        """Generate verification token for new anonymous feedback"""
        if not self.pk and not self.user and not self.email_verified:
            self.email_verification_token = uuid.uuid4().hex
            self.email_verification_sent_at = timezone.now()
        super().save(*args, **kwargs)


class FeedbackReply(BaseModel):
    """
    Feedback Reply Model
    Stores replies to feedback (both official replies and internal notes)
    """
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name=_("Related Feedback")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='feedback_replies',
        verbose_name=_("Replier"),
        null=True
    )
    content = models.TextField(
        _("Reply Content")
    )
    is_internal_note = models.BooleanField(
        _("Is Internal Note"), 
        default=False, 
        help_text="Internal notes are not sent to users"
    )
    
    # Email Tracking
    email_sent = models.BooleanField(
        _("Email Sent"), 
        default=False
    )
    email_sent_at = models.DateTimeField(
        _("Email Sent At"), 
        blank=True, 
        null=True
    )
    email_error = models.TextField(
        _("Email Error"), 
        blank=True, 
        null=True
    )
    email_retry_count = models.PositiveSmallIntegerField(
        _("Email Retry Count"), 
        default=0
    )
    
    class Meta:
        db_table = 'feedback_reply'
        verbose_name = _('Feedback Reply')
        verbose_name_plural = _('Feedback Replies')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['feedback', 'is_internal_note']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Reply to: {self.feedback.title[:50]}"
    
    def save(self, *args, **kwargs):
        """Update feedback reply count"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and not self.is_internal_note:
            self.feedback.reply_count += 1
            self.feedback.save(update_fields=['reply_count'])


class FeedbackStatusHistory(BaseModel):
    """
    Feedback Status History Model
    Tracks all status changes for audit and analysis
    """
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_("Related Feedback")
    )
    from_status = models.CharField(
        _("From Status"), 
        max_length=20, 
        choices=Feedback.STATUS_CHOICES, 
        blank=True, 
        null=True
    )
    to_status = models.CharField(
        _("To Status"), 
        max_length=20, 
        choices=Feedback.STATUS_CHOICES
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='feedback_status_changes',
        verbose_name=_("Changed By"),
        null=True
    )
    reason = models.TextField(
        _("Change Reason"), 
        blank=True, 
        null=True
    )
    
    class Meta:
        db_table = 'feedback_status_history'
        verbose_name = _('Feedback Status History')
        verbose_name_plural = _('Feedback Status Histories')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['feedback', 'created_at']),
            models.Index(fields=['changed_by']),
        ]
    
    def __str__(self):
        return f"{self.feedback.title}: {self.from_status} → {self.to_status}"


class FeedbackAttachment(BaseModel):
    """
    Feedback Attachment Model
    Stores files attached to feedback (screenshots, logs, etc.)
    """
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_("Related Feedback")
    )
    file = models.FileField(
        _("File"),
        upload_to='feedbacks/attachments/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'pdf', 
                                   'doc', 'docx', 'txt', 'log', 'zip']
            )
        ]
    )
    filename = models.CharField(
        _("Original Filename"), 
        max_length=255
    )
    file_size = models.PositiveIntegerField(
        _("File Size"), 
        help_text="File size in bytes"
    )
    mime_type = models.CharField(
        _("MIME Type"), 
        max_length=100, 
        blank=True, 
        null=True
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='uploaded_attachments',
        verbose_name=_("Uploaded By"),
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'feedback_attachment'
        verbose_name = _('Feedback Attachment')
        verbose_name_plural = _('Feedback Attachments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['feedback']),
            models.Index(fields=['uploaded_by']),
        ]
    
    def __str__(self):
        return f"{self.filename} ({self.feedback.title[:30]})"


class FeedbackVote(BaseModel):
    """
    Feedback Vote Model
    Tracks user votes on feedback to identify popular issues
    """
    VOTE_CHOICES = [
        (1, 'Upvote'),
        (-1, 'Downvote'),
    ]
    
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name=_("Related Feedback")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedback_votes',
        verbose_name=_("Voter")
    )
    vote_type = models.SmallIntegerField(
        _("Vote Type"), 
        choices=VOTE_CHOICES, 
        default=1
    )
    
    class Meta:
        db_table = 'feedback_vote'
        verbose_name = _('Feedback Vote')
        verbose_name_plural = _('Feedback Votes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['feedback', 'user']),
            models.Index(fields=['user']),
        ]
        unique_together = [['feedback', 'user']]
    
    def __str__(self):
        vote_display = "👍" if self.vote_type == 1 else "👎"
        return f"{self.user.username} {vote_display} {self.feedback.title[:30]}"
    
    def save(self, *args, **kwargs):
        """Update feedback vote count"""
        is_new = self.pk is None
        old_vote = None
        
        if not is_new:
            old_vote = FeedbackVote.objects.get(pk=self.pk).vote_type
        
        super().save(*args, **kwargs)
        
        # Update vote count
        if is_new:
            self.feedback.vote_count += self.vote_type
        elif old_vote != self.vote_type:
            self.feedback.vote_count = self.feedback.vote_count - old_vote + self.vote_type
        
        self.feedback.save(update_fields=['vote_count'])
    
    def delete(self, *args, **kwargs):
        """Update feedback vote count when deleting"""
        self.feedback.vote_count -= self.vote_type
        self.feedback.save(update_fields=['vote_count'])
        super().delete(*args, **kwargs)


# ===================== Email Management Models =====================

class FeedbackEmailLog(BaseModel):
    """
    Feedback Email Log Model
    Tracks all email communications related to feedback
    """
    EMAIL_TYPE_CHOICES = [
        ('reply', 'Reply Notification'),
        ('status_change', 'Status Change'),
        ('verification', 'Email Verification'),
        ('summary', 'Summary Report'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='email_logs',
        verbose_name=_("Related Feedback"),
        blank=True,
        null=True
    )
    email_type = models.CharField(
        _("Email Type"), 
        max_length=20, 
        choices=EMAIL_TYPE_CHOICES
    )
    recipient = models.EmailField(
        _("Recipient Email")
    )
    subject = models.CharField(
        _("Subject"), 
        max_length=500
    )
    content = models.TextField(
        _("Email Content")
    )
    status = models.CharField(
        _("Status"), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    sent_at = models.DateTimeField(
        _("Sent At"), 
        blank=True, 
        null=True
    )
    error_message = models.TextField(
        _("Error Message"), 
        blank=True, 
        null=True
    )
    retry_count = models.PositiveSmallIntegerField(
        _("Retry Count"), 
        default=0
    )
    celery_task_id = models.CharField(
        _("Celery Task ID"), 
        max_length=255, 
        blank=True, 
        null=True
    )
    
    class Meta:
        db_table = 'feedback_email_log'
        verbose_name = _('Feedback Email Log')
        verbose_name_plural = _('Feedback Email Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['feedback', 'email_type']),
            models.Index(fields=['status']),
            models.Index(fields=['recipient']),
            models.Index(fields=['sent_at']),
        ]
    
    def __str__(self):
        return f"{self.get_email_type_display()} to {self.recipient}"


class EmailTemplate(BaseModel):
    """
    Email Template Model
    Configurable email templates for different notification types
    """
    TEMPLATE_TYPE_CHOICES = [
        ('reply', 'Reply Notification'),
        ('status_change', 'Status Change'),
        ('verification', 'Email Verification'),
        ('welcome', 'Welcome Email'),
    ]
    
    name = models.CharField(
        _("Template Name"), 
        max_length=100
    )
    template_type = models.CharField(
        _("Template Type"), 
        max_length=20, 
        choices=TEMPLATE_TYPE_CHOICES
    )
    subject = models.CharField(
        _("Email Subject"), 
        max_length=500, 
        help_text="Supports variables like {feedback_title}, {status}"
    )
    body_html = models.TextField(
        _("HTML Body"), 
        help_text="HTML email template with variables"
    )
    body_text = models.TextField(
        _("Plain Text Body"), 
        blank=True, 
        null=True, 
        help_text="Plain text version of email"
    )
    is_active = models.BooleanField(
        _("Is Active"), 
        default=True
    )
    variables = models.JSONField(
        _("Available Variables"), 
        default=dict, 
        blank=True, 
        help_text="List of available template variables"
    )
    
    class Meta:
        db_table = 'feedback_email_template'
        verbose_name = _('Email Template')
        verbose_name_plural = _('Email Templates')
        ordering = ['template_type', 'name']
        indexes = [
            models.Index(fields=['tenant', 'template_type', 'is_active']),
        ]
        unique_together = [['tenant', 'template_type', 'name']]
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def render(self, context):
        """Render template with given context"""
        import re
        
        subject = self.subject
        body_html = self.body_html
        body_text = self.body_text or body_html
        
        # Simple variable replacement
        for key, value in context.items():
            pattern = r'\{' + key + r'\}'
            subject = re.sub(pattern, str(value), subject)
            body_html = re.sub(pattern, str(value), body_html)
            body_text = re.sub(pattern, str(value), body_text)
        
        return {
            'subject': subject,
            'body_html': body_html,
            'body_text': body_text
        }