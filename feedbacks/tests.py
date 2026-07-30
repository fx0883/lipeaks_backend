from django.test import TestCase
from django.urls import reverse

from applications.models import Application
from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member


class FeedbackSubmitPageTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.member = Member.objects.create(
            username="feedback_member",
            email="feedback-member@example.com",
            tenant=self.tenant,
        )
        self.application = Application.objects.create(
            tenant=self.tenant,
            name="Feedback App",
            code="feedback-app",
            is_active=True,
        )

    def test_feedback_submit_page_accepts_project_member_jwt_token(self):
        member_token = generate_jwt_token(self.member)["access_token"]

        response = self.client.get(
            reverse("feedbacks:feedback-submit"),
            {
                "tenant_id": self.tenant.id,
                "application_id": self.application.id,
                "member_token": member_token,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["member"].id, self.member.id)
        self.assertTrue(response.context["has_member_info"])
        self.assertEqual(response.context["form"].initial["contact_email"], self.member.email)
