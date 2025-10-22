"""
Management command to initialize default email templates for all tenants
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from tenants.models import Tenant
from feedbacks.models import EmailTemplate
from feedbacks.services import EmailService


class Command(BaseCommand):
    help = 'Initialize default email templates for all tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=int,
            help='Specific tenant ID to initialize templates for'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of templates even if they exist'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        tenant_id = options.get('tenant')
        force = options.get('force', False)
        
        if tenant_id:
            try:
                tenant = Tenant.objects.get(pk=tenant_id)
                tenants = [tenant]
                self.stdout.write(f"Initializing templates for tenant: {tenant.name}")
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Tenant with ID {tenant_id} not found"))
                return
        else:
            tenants = Tenant.objects.filter(is_active=True)
            self.stdout.write(f"Initializing templates for {tenants.count()} active tenants")
        
        created_count = 0
        skipped_count = 0
        
        for tenant in tenants:
            # Check if templates already exist
            existing_templates = EmailTemplate.objects.filter(
                tenant=tenant,
                template_type__in=['reply', 'status_change', 'verification']
            ).count()
            
            if existing_templates > 0 and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping {tenant.name} - templates already exist (use --force to recreate)"
                    )
                )
                skipped_count += 1
                continue
            
            # Delete existing templates if force is True
            if force:
                EmailTemplate.objects.filter(tenant=tenant).delete()
            
            # Create default templates
            templates = EmailService.create_default_templates(tenant)
            created_count += len(templates)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {len(templates)} templates for {tenant.name}"
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary: Created {created_count} templates, skipped {skipped_count} tenants"
            )
        )
