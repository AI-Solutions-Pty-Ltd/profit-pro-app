from django import forms

from app.Account.models import Account
from app.BillOfQuantities.models import PaymentCertificate
from app.core.Utilities.widgets import SearchableSelectWidget
from app.Project.models import Company, ProjectCompanyUserRole


class PaymentCertificateApprovedDateForm(forms.ModelForm):
    """Form for editing only the approved_on date."""

    class Meta:
        model = PaymentCertificate
        fields = ["approved_on", "assessment_date"]
        widgets = {
            "approved_on": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "block w-fit border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
                }
            ),
            "assessment_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "block w-fit border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
                }
            ),
        }
        labels = {
            "approved_on": "Approval Date",
            "assessment_date": "Assessment Date",
        }


class ProjectClientForm(forms.Form):
    """Form to select a client for a project."""

    client = forms.ModelChoiceField(
        queryset=Company.objects.none(),
        widget=SearchableSelectWidget(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
            },
            create_url=True,
            resource_type="client",
        ),
        required=False,
        help_text="Select a client company to associate with this project.",
    )

    def __init__(self, *args, **kwargs):
        kwargs.pop("project", None)
        user: Account | None = kwargs.pop("user", None)

        # Pop instance before calling super() to avoid passing it to Form
        self.instance = kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)
        self.fields["client"].label = "Client Company"

        if user:
            if user.has_demo_permission:
                Company.ensure_demo_companies(user=user)

            projects = user.get_projects

            # Filter to show client companies that are either associated with the user's projects or account
            from django.db.models import Q

            condition = Q(client_projects__in=projects) | Q(users=user)
            if user.has_demo_permission:
                condition |= Q(
                    registration_number__in=["DEMO-CLIENT", f"DEMO-CLIENT-{user.pk}"]
                )

            queryset = Company.objects.filter(
                condition,
                type=Company.Type.CLIENT,
            ).order_by("name")

            # Type: ModelChoiceField has queryset attribute
            client_field = self.fields["client"]
            if hasattr(client_field, "queryset"):
                client_field.queryset = queryset.distinct()  # type: ignore
        else:
            # Fallback for all client companies if user is not provided
            client_field = self.fields["client"]
            if hasattr(client_field, "queryset"):
                client_field.queryset = Company.objects.filter(  # type: ignore
                    type=Company.Type.CLIENT
                ).order_by("name")


class ProjectCompanyUserRoleForm(forms.ModelForm):
    """Form to assign a user to a company on a project with a role."""

    class Meta:
        model = ProjectCompanyUserRole
        fields = ["user", "role"]
        widgets = {
            "user": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "role": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        self.company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if self.company:
            # Only allow selecting users who belong to the company
            self.fields["user"].queryset = self.company.users.all().order_by(
                "first_name", "last_name"
            )
        else:
            self.fields["user"].queryset = Account.objects.none()

        if self.instance and self.instance.pk:
            self.fields["user"].disabled = True


class CompanyUserInviteForm(forms.Form):
    """Form for inviting a user to a stakeholder company."""

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "user@example.com",
            }
        ),
        label="Email Address",
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "John",
            }
        ),
        label="First Name",
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "Doe",
            }
        ),
        label="Last Name (Optional)",
    )
    primary_contact = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "+27123456789",
            }
        ),
        label="Phone Number",
    )
