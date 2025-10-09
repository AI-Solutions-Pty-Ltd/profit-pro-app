from django.contrib import admin

from .models import (
    ActualTransaction,
    Bill,
    LineItem,
    Package,
    PaymentCertificate,
    Structure,
)

admin.site.register(Structure)
admin.site.register(Bill)
admin.site.register(Package)
admin.site.register(LineItem)
admin.site.register(PaymentCertificate)
admin.site.register(ActualTransaction)
