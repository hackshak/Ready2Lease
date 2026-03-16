import qrcode
import os
from django.conf import settings


def generate_qr(report_id):

    verify_url = "https://ready2lease.com.au/"  # homepage

    qr = qrcode.make(verify_url)

    folder = os.path.join(settings.MEDIA_ROOT, "qr_codes")
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, f"{report_id}.png")

    qr.save(file_path)

    return file_path