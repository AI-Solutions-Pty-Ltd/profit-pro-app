from django.contrib import admin

from .models import Bill, LineItem, Package, Structure

admin.site.register(Structure)
admin.site.register(Bill)
admin.site.register(Package)
admin.site.register(LineItem)
