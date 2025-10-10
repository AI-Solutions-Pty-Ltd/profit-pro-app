# Payment Certificate PDF Download Feature

## Overview
Added a "Download PDF" button to the payment certificate detail page that generates and downloads a formal PDF document.

## Changes Made

### 1. Views (`app/BillOfQuantities/views_payment_certificate.py`)
Added `PaymentCertificateDownloadPDFView`:
- Authenticates user with `LoginRequiredMixin`
- Validates user owns the project via `GetProjectMixin`
- Generates PDF using `generate_payment_certificate_pdf()`
- Returns PDF as file download with proper filename

### 2. URLs (`app/BillOfQuantities/urls.py`)
Added new URL pattern:
```python
path(
    "project/<int:project_pk>/payment-certificates/<int:pk>/download-pdf/",
    views_payment_certificate.PaymentCertificateDownloadPDFView.as_view(),
    name="payment-certificate-download-pdf",
)
```

### 3. Template (`payment_certificate/payment_certificate_detail.html`)
Added prominent "Download PDF" button in the header:
- Styled with indigo background (primary action)
- Uses heroicon "arrow-down-tray" icon
- Positioned before navigation buttons

### 4. Tasks (`app/BillOfQuantities/tasks.py`)
Updated `generate_payment_certificate_pdf()`:
- Saves PDF to `MEDIA_ROOT/payment_certificates/`
- Creates directory if it doesn't exist
- Returns file path for the saved PDF
- Filename format: `payment_certificate_{certificate_number}.pdf`

## File Storage
PDFs are saved to: `{MEDIA_ROOT}/payment_certificates/payment_certificate_{number}.pdf`

## Usage
1. Navigate to any payment certificate detail page
2. Click the "Download PDF" button in the top right
3. PDF will be generated and downloaded automatically

## Security
- User authentication required (`LoginRequiredMixin`)
- User must own the project (validated via `GetProjectMixin`)
- No direct file path access - files served through Django view

## Future Enhancements
- Add option to email PDF to client
- Add PDF preview before download
- Cache generated PDFs to avoid regeneration
- Add watermark for draft certificates
