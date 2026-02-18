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
    PasswordResetView as BasePasswordResetView,
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import CreateView

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
