from app.BillOfQuantities.exporters.detailed_report_exporter import (
    export_detailed_report_to_xlsx,
)
from app.BillOfQuantities.models import PaymentCertificate

# Find the specific PC from the screenshot
pc = PaymentCertificate.objects.filter(
    certificate_number=1, project__name__icontains="School Project"
).first()
if not pc:
    print("Could not find PC")
else:
    print(f"Exporting PC: {pc.id}")
    wb = export_detailed_report_to_xlsx(pc, is_abridged=True)
    wb.save("test_export_2.xlsx")
