# feedbacks/management/commands/test_email_validation.py

from django.core.management.base import BaseCommand
from ...utils import EmailValidator


class Command(BaseCommand):
    help = '测试邮件地址验证功能'

    def handle(self, *args, **options):
        # 测试用例
        test_cases = [
            # Valid email addresses
            ('user@example.org', True, 'Normal email address'),
            ('john.doe@company.com', True, 'Email with dots'),
            ('user+tag@domain.co.uk', True, 'Email with plus and multi-level domain'),
            ('test_user@sub.domain.com', True, 'Email with underscore and subdomain'),
            
            # Invalid email addresses  
            ('', False, 'Empty string'),
            ('invalid', False, 'No @ symbol'),
            ('user@', False, 'No domain'),
            ('@domain.com', False, 'No username'),
            ('user@example.com@extra', False, 'Multiple @ symbols'),
            ('user space@domain.com', False, 'Contains space'),
            ('user@domain', False, 'No top-level domain'),
            
            # Test emails (will be rejected)
            ('test@example.com', False, 'Test email example.com'),
            ('demo@test.com', False, 'Test email test.com'),
            ('user@localhost', False, 'Localhost'),
            ('noreply@company.com', False, 'No-reply email'),
            ('test@tempmail.org', False, 'Temporary email'),
            
            # Length limit tests
            ('a' * 65 + '@domain.com', False, 'Username too long'),
            ('user@' + 'a' * 250 + '.com', False, 'Total length too long'),
        ]
        
        self.stdout.write(
            self.style.SUCCESS('Starting email validation tests...\n')
        )
        
        passed = 0
        failed = 0
        
        for email, expected, description in test_cases:
            result = EmailValidator.is_valid_email(email)
            
            if result == expected:
                self.stdout.write(
                    self.style.SUCCESS(f'[PASS] {description}')
                )
                self.stdout.write(f'    Email: "{email}" -> {result}\n')
                passed += 1
            else:
                self.stdout.write(
                    self.style.ERROR(f'[FAIL] {description}')
                )
                self.stdout.write(f'    Email: "{email}" -> Expected: {expected}, Actual: {result}\n')
                failed += 1
        
        # Test logging functionality
        self.stdout.write('\nTesting logging functionality:')
        self.stdout.write('Valid email:')
        EmailValidator.validate_and_log('user@valid.com', ' in test')
        
        self.stdout.write('Invalid email:')
        EmailValidator.validate_and_log('invalid@example.com', ' in test')
        
        # Summary
        self.stdout.write(f'\nSummary:')
        self.stdout.write(
            self.style.SUCCESS(f'Passed: {passed}')
        )
        if failed > 0:
            self.stdout.write(
                self.style.ERROR(f'Failed: {failed}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('All tests passed!')
            )
