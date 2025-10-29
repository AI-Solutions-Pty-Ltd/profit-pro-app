from django.contrib import admin

from app.Cost.models import ActualCost, Cost

# Register your models here.

admin.site.register(Cost)
admin.site.register(ActualCost)
