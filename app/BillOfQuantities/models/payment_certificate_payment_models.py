from app.core.Utilities.models import BaseModel
from django.db import models


class PaymentCertificatePayment(BaseModel):
    """
    Payments are not linked directly to a payment certificate

    Only to a project
    """

    project = models.ForeignKey("Project.Project", on_delete=models.CASCADE)

    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
