#!/usr/bin/env python
"""
Test SMTP connection and email sending
Used to diagnose mail configuration issues
"""
import os
import sys
import django
import ssl

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
import smtplib

def test_smtp_connection():
    """Test SMTP connection"""
    print("[SMTP Test] Starting SMTP connection test...")
    print(f"[SMTP Test] Host: {settings.EMAIL_HOST}")
    print(f"[SMTP Test] Port: {settings.EMAIL_PORT}")
    print(f"[SMTP Test] Use SSL: {settings.EMAIL_USE_SSL}")
    print(f"[SMTP Test] From: {settings.DEFAULT_FROM_EMAIL}")
    
    try:
        if settings.EMAIL_USE_SSL:
            print("[SMTP Test] Creating SSL SMTP connection...")
            # Try with default SSL context
            server = smtplib.SMTP_SSL(
                settings.EMAIL_HOST,
                settings.EMAIL_PORT,
                timeout=30
            )
        else:
            print("[SMTP Test] Creating TLS SMTP connection...")
            server = smtplib.SMTP(
                settings.EMAIL_HOST,
                settings.EMAIL_PORT,
                timeout=30
            )
            server.starttls()
        
        print("[SMTP Test] [OK] SMTP connection established")
        
        # Try to login
        username = settings.EMAIL_HOST_USER
        password = settings.EMAIL_HOST_PASSWORD
        
        if not username or not password:
            print("[SMTP Test] [WARNING] EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not set")
            return False
        
        print(f"[SMTP Test] Logging in with user: {username}")
        server.login(username, password)
        print("[SMTP Test] [OK] Authentication successful")
        
        server.quit()
        return True
        
    except ssl.SSLError as e:
        print(f"[SMTP Test] [FAILED] SSL Error: {str(e)}")
        print("[SMTP Test] Try changing to TLS instead of SSL")
        print("[SMTP Test] Set EMAIL_PORT=587, EMAIL_USE_SSL=False, EMAIL_USE_TLS=True")
        return False
    except smtplib.SMTPAuthenticationError as e:
        print(f"[SMTP Test] [FAILED] Authentication Error: {str(e)}")
        print("[SMTP Test] Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
        return False
    except Exception as e:
        print(f"[SMTP Test] [FAILED] Unexpected error: {type(e).__name__}: {str(e)}")
        return False


def test_send_email(to_email):
    """Test sending email"""
    print(f"\n[Email Test] Sending test email to: {to_email}")
    
    try:
        msg = EmailMultiAlternatives(
            subject='[Test] Email Configuration Test',
            body='This is a test email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email]
        )
        msg.attach_alternative('<p>This is a test email.</p>', "text/html")
        msg.send()
        print("[Email Test] [OK] Email sent successfully")
        return True
    except Exception as e:
        print(f"[Email Test] [FAILED] {type(e).__name__}: {str(e)}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("SMTP Connection and Email Test")
    print("=" * 60)
    
    # Test SMTP connection
    if not test_smtp_connection():
        sys.exit(1)
    
    # Test send email
    test_email = input("\nEnter test email address (or press Enter to skip): ").strip()
    if test_email:
        test_send_email(test_email)
    
    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)
