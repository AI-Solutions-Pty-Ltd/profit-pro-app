"""Tests for notices context processor."""

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from app.core.Utilities.context_processors import custom_context_processor
from app.Notices.models import Notice

Account = get_user_model()


class TestNoticesContextProcessor(TestCase):
    """Test cases for notices context processor."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = Account.objects.create_user(  # type: ignore
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            primary_contact="+1234567890",
        )

    def test_notice_count_with_no_notices(self):
        """Test notice count when no notices exist."""
        request = self.factory.get("/")
        request.user = self.user

        context = custom_context_processor(request)

        assert context["NOTICE_COUNT"] == 5  # Only dummy items

    def test_notice_count_with_actual_notices(self):
        """Test notice count includes actual notices."""
        # Create some notices
        Notice.objects.create(text="Test Notice 1")
        Notice.objects.create(text="Test Notice 2")

        request = self.factory.get("/")
        request.user = self.user

        context = custom_context_processor(request)

        assert context["NOTICE_COUNT"] == 7  # 2 actual + 5 dummy

    def test_context_processor_includes_other_vars(self):
        """Test that context processor includes other expected variables."""
        request = self.factory.get("/")
        request.user = self.user

        context = custom_context_processor(request)

        assert "SITE_NAME" in context
        assert "ROLES" in context
        assert "NOTICE_COUNT" in context
