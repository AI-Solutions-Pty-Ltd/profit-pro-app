"""Management command to reset stuck PDF generation flags."""

from django.core.management.base import BaseCommand

from app.BillOfQuantities.models import PaymentCertificate


class Command(BaseCommand):
    """Reset PDF generation flags for payment certificates."""

    help = "Reset stuck PDF generation flags for payment certificates"

    def add_arguments(self, parser):
        parser.add_argument(
            "--certificate-id",
            type=int,
            help="Reset flags for specific certificate ID",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Reset flags for all certificates",
        )

    def handle(self, *args, **options):
        certificate_id = options.get("certificate_id")
        reset_all = options.get("all")

        if certificate_id:
            try:
                cert = PaymentCertificate.objects.get(id=certificate_id)
                self._reset_flags(cert)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Reset flags for certificate #{cert.certificate_number}"
                    )
                )
            except PaymentCertificate.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Certificate with ID {certificate_id} not found")
                )
        elif reset_all:
            certs = PaymentCertificate.objects.filter(
                pdf_generating=True
            ) | PaymentCertificate.objects.filter(abridged_pdf_generating=True)
            count = certs.count()
            for cert in certs:
                self._reset_flags(cert)
            self.stdout.write(
                self.style.SUCCESS(f"Reset flags for {count} certificate(s)")
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    "Please specify --certificate-id or --all to reset flags"
                )
            )

    def _reset_flags(self, certificate):
        """Reset generation flags for a certificate."""
        if certificate.pdf_generating:
            self.stdout.write("  Resetting pdf_generating flag")
            certificate.pdf_generating = False
        if certificate.abridged_pdf_generating:
            self.stdout.write("  Resetting abridged_pdf_generating flag")
            certificate.abridged_pdf_generating = False
        certificate.save()
