from typing import TYPE_CHECKING, cast

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import (
    BaseUserCreationForm,
)
from django.contrib.auth.forms import (
    PasswordResetForm as BasePasswordResetForm,
)
from django.contrib.auth.views import (
    LoginView as BaseLoginView,
)
from django.contrib.auth.views import (
    LogoutView as BaseLogoutView,
)
from django.contrib.auth.views import (
    PasswordResetConfirmView as BasePasswordResetConfirmView,
)
from django.contrib.auth.views import (
    PasswordResetView as BasePasswordResetView,
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, View

from app.Account.models import Account
from app.Account.services import send_verification_email

if TYPE_CHECKING:
    pass


class CustomPasswordResetForm(BasePasswordResetForm):
    """Custom password reset form that builds absolute URLs."""

    def save(
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.html",
        use_https=False,
        token_generator=None,
        from_email=None,
        request=None,
        html_email_template_name=None,
        extra_email_context=None,
    ):
        """
        Override save to pass request to send_mail context.
        """
        email = self.cleaned_data["email"]
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override

        user = next(iter(self.get_users(email)), None)
        if user:
            # Build the context with request
            context = {
                "email": email,
                "domain": domain,
                "site_name": site_name,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": token_generator.make_token(user) if token_generator else "",
                "protocol": "https" if use_https else "http",
                "request": request,  # Add request to context
                **(extra_email_context or {}),
            }

            self.send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                email,
                html_email_template_name=html_email_template_name,
            )

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Override send_mail to build absolute URL like email verification.
        """
        # Build absolute reset link
        reset_link = context["request"].build_absolute_uri(
            reverse(
                "users:auth:password_reset_confirm",
                kwargs={"uidb64": context["uid"], "token": context["token"]},
            )
        )

        # Update context with the absolute URL
        context["reset_link"] = reset_link
        context["site_name"] = settings.SITE_NAME

        # Render email
        subject = render_to_string(subject_template_name, context).strip()
        html_message = render_to_string(html_email_template_name or "", context)

        # Send email
        send_mail(
            subject=subject,
            message="",
            from_email=from_email,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )


class RegisterView(CreateView):
    """Registration page view for new users."""

    class RegisterForm(BaseUserCreationForm):
        username = None
        email = forms.EmailField(
            widget=forms.EmailInput(attrs={"placeholder": "Enter your email address"})
        )
        first_name = forms.CharField(
            max_length=150,
            required=True,
            widget=forms.TextInput(attrs={"placeholder": "Enter your first name"}),
        )
        last_name = forms.CharField(
            max_length=150,
            required=True,
            widget=forms.TextInput(attrs={"placeholder": "Enter your last name"}),
        )
        password1 = forms.CharField(
            widget=forms.PasswordInput(attrs={"placeholder": "Create a password"})
        )
        password2 = forms.CharField(
            widget=forms.PasswordInput(attrs={"placeholder": "Confirm your password"})
        )

        class Meta:
            model = Account
            fields = ["email", "first_name", "last_name", "password1", "password2"]

        def clean_email(self):
            email = self.cleaned_data["email"]
            existing_user = Account.objects.filter(email=email).first()

            if existing_user:
                if existing_user.email_verified:
                    raise forms.ValidationError("This email is already in use.")
                else:
                    # Email exists but not verified - we'll handle this in form_valid
                    self.existing_unverified_user = existing_user
            return email

    template_name = "auth/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": f"Register - {settings.SITE_NAME or 'Profit Pro'}",
                "next": self.request.GET.get("next", "home"),
            }
        )
        return context

    def form_valid(self, form):
        # Check if we have an existing unverified user
        if hasattr(form, "existing_unverified_user") and form.existing_unverified_user:
            # Send verification email to existing user
            send_verification_email(self.request, form.cleaned_data["email"])
            messages.info(
                self.request,
                "An account with this email already exists but hasn't been verified. "
                "We've sent a new verification email. Please check your inbox.",
            )
            return redirect("home")

        # Create new user
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Registration successful. Please check your email to verify your account.",
        )

        # Send verification email
        send_verification_email(self.request, form.instance.email)

        return response


class LoginView(BaseLoginView):
    """Custom login view that checks email verification."""

    template_name = "auth/login.html"

    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users home with a message."""
        if request.user.is_authenticated:
            user = cast(Account, request.user)
            messages.info(
                request,
                f"You are already logged in as {user.get_full_name() or user.email}.",
            )
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Check email verification before logging in."""
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")

        # Authenticate user
        user: Account = authenticate(self.request, username=username, password=password)  # type: ignore

        if user is not None:
            if not user.email_verified:
                # Email not verified - send verification email
                send_verification_email(self.request, user.email)
                messages.info(
                    self.request,
                    "Your email address has not been verified. "
                    "We've sent a new verification email. Please check your inbox.",
                )
                return redirect("users:auth:login")

            # Email is verified - proceed with login
            login(self.request, user)
            messages.success(
                self.request, f"Welcome back, {user.get_full_name() or user.email}!"
            )

            # Redirect to home page
            return redirect("home")

        # Authentication failed
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": f"Login - {settings.SITE_NAME or 'Profit Pro'}",
                "next": self.request.GET.get("next", "home"),
            }
        )
        return context


class PasswordResetView(BasePasswordResetView):
    """Custom password reset view that builds absolute URLs."""

    template_name = "auth/password_reset_form.html"
    subject_template_name = "auth/password_reset_subject.txt"
    email_template_name = "auth/password_reset_email.html"
    html_email_template_name = "auth/password_reset_email.html"
    success_url = "done/"
    form_class = CustomPasswordResetForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": f"Reset Password - {settings.SITE_NAME or 'Profit Pro'}",
            }
        )
        return context


class LogoutView(BaseLogoutView):
    """Custom logout view that adds a success message."""

    next_page = "home"

    def dispatch(self, request, *args, **kwargs):
        """Add success message before logging out."""
        if request.user.is_authenticated:
            # Cast to Account type for type checker
            user = cast(Account, request.user)
            messages.success(
                request,
                f"You have been successfully logged out. Goodbye, {user.get_full_name() or user.email}!",
            )
        return super().dispatch(request, *args, **kwargs)


class PasswordResetConfirmView(BasePasswordResetConfirmView):
    """Custom password reset confirm view that verifies email and logs in user."""

    template_name = "auth/password_reset_confirm.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        """Save the user, verify email, and log them in."""
        # Save the new password
        response = super().form_valid(form)

        # Get the user object
        user = cast(Account, self.user)

        # Verify the user's email
        if not user.email_verified:
            user.email_verified = True
            user.save()
            messages.success(
                self.request,
                "Your email has been verified and your password has been reset successfully!",
            )
        else:
            messages.success(
                self.request,
                "Your password has been reset successfully!",
            )

        # Log the user in
        login(self.request, user)
        messages.info(
            self.request,
            f"You have been logged in as {user.get_full_name() or user.email}.",
        )

        return response


@method_decorator(csrf_exempt, name="dispatch")
class SedgeProWebhookView(View):
    """Secure webhook endpoint for SedgePro user invitations."""

    def post(self, request, *args, **kwargs):
        import json

        from django.contrib.auth.models import Group
        from django.contrib.auth.tokens import default_token_generator
        from django.db import transaction
        from django.http import JsonResponse

        from app.Project.models import Company

        # 1. Authenticate with X-SedgePro-API-Key
        api_key = request.headers.get("X-SedgePro-API-Key")
        if not api_key or api_key != settings.SEDGEPRO_API_KEY:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        # 2. Parse and validate JSON payload
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)

        # Support Supabase Database Webhook wrapper format
        if isinstance(data, dict) and "record" in data:
            data = data["record"] or {}

        email = data.get("email") or data.get("user_email")
        client_reference = data.get("client_reference")

        if not email or not client_reference:
            return JsonResponse(
                {"error": "Missing email or client_reference"}, status=400
            )

        # 3. Resolve target company client
        try:
            company = Company.objects.get(
                registration_number=client_reference, type=Company.Type.CLIENT
            )
        except Company.DoesNotExist:
            return JsonResponse({"error": "Company not found"}, status=400)

        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        primary_contact = data.get("primary_contact", "")

        # 4. Atomic transaction block
        try:
            with transaction.atomic():
                # Check if user already exists
                email_lower = email.lower()
                user_exists = True
                try:
                    user = Account.objects.get(email=email_lower)
                except Account.DoesNotExist:
                    # Create new user
                    user = Account.objects.create_user(
                        email=email_lower,
                        first_name=first_name,
                        last_name=last_name,
                        primary_contact=primary_contact or "+27820000000",
                        type=Account.Type.CLIENT,
                    )
                    user.set_unusable_password()
                    user.save()
                    user_exists = False

                # Ensure added to consultant group
                consultant_group, _ = Group.objects.get_or_create(name="consultant")
                user.groups.add(consultant_group)

                # Ensure linked to Company
                if company.users.filter(pk=user.pk).exists():
                    # Idempotent case: already linked
                    return JsonResponse(
                        {
                            "status": "success",
                            "message": "User already associated with company",
                        }
                    )

                company.users.add(user)

                # 5. Send onboarding/invitation email
                if settings.USE_EMAIL:
                    protocol = "https" if request.is_secure() else "http"
                    domain = request.get_host()

                    if user_exists:
                        # Existing user: send notification
                        context = {
                            "user": user,
                            "site_name": settings.SITE_NAME,
                            "client_name": company.name,
                            "protocol": protocol,
                            "domain": domain,
                        }
                        subject = f"You've been added to {company.name} on {settings.SITE_NAME}"
                        html_message = render_to_string(
                            "client/client_added_email.html", context
                        )
                    else:
                        # New user: send setup password invite
                        token = default_token_generator.make_token(user)
                        uid = urlsafe_base64_encode(force_bytes(user.pk))
                        context = {
                            "user": user,
                            "protocol": protocol,
                            "domain": domain,
                            "uid": uid,
                            "token": token,
                            "site_name": settings.SITE_NAME,
                            "expiry_hours": 24,
                            "client_name": company.name,
                        }
                        subject = f"You've been invited to {company.name} on {settings.SITE_NAME}"
                        html_message = render_to_string(
                            "client/password_reset_email.html", context
                        )

                    send_mail(
                        subject=subject,
                        message="",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )

                if user_exists:
                    return JsonResponse(
                        {
                            "status": "success",
                            "message": "User linked to company",
                        }
                    )
                else:
                    return JsonResponse(
                        {
                            "status": "success",
                            "message": "User invited",
                        }
                    )

        except Exception as e:
            return JsonResponse(
                {"error": f"Internal processing error: {str(e)}"}, status=500
            )
