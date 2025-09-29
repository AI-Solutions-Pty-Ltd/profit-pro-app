from django.contrib import admin
from django.contrib.auth.hashers import make_password
from import_export.admin import ImportExportModelAdmin

from .models import Account, Suburb, Town


@admin.register(Account)
class AccountAdmin(ImportExportModelAdmin):
    def save_model(self, request, obj, form, change):
        """Change password only if the password field is updated or
        else it will always rehash the password and GL figuring that out LOL
        """
        if "password" in form.changed_data:
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)

    search_fields = ("email", "first_name", "last_name", "email")


admin.site.register(Suburb, ImportExportModelAdmin)
admin.site.register(Town, ImportExportModelAdmin)
