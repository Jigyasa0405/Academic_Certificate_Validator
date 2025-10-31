# backend/app/qr_verification.py
import cv2
import numpy as np
from .database import get_db_connection


def extract_qr_region(image, qr_roi):
    """Extract QR code region from certificate using ROI coordinates"""
    height, width = image.shape[:2]
    x_start = int(qr_roi[0] * width)
    y_start = int(qr_roi[1] * height)
    x_end = int(qr_roi[2] * width)
    y_end = int(qr_roi[3] * height)
    return image[y_start:y_end, x_start:x_end]


def read_qr_code_opencv(qr_region):
    """Read QR code using OpenCV's built-in QR code detector"""
    # Convert to grayscale for better detection
    if len(qr_region.shape) == 3:
        gray = cv2.cvtColor(qr_region, cv2.COLOR_BGR2GRAY)
    else:
        gray = qr_region

    # Initialize QR code detector
    qr_detector = cv2.QRCodeDetector()

    # Detect and decode QR code
    data, points, _ = qr_detector.detectAndDecode(gray)

    if points is not None and data:
        return data
    return None


def parse_qr_data(qr_data):
    """Parse QR data that contains labels like 'Certificate ID: ... Digital Hash: ...'"""
    if not qr_data:
        return None, None

    cert_id = None
    digital_hash = None

    # Handle multi-line format with labels
    lines = qr_data.split('\n')

    for i, line in enumerate(lines):
        line = line.strip()

        if line.startswith('Certificate ID:'):
            cert_id = line.replace('Certificate ID:', '').strip()

        elif line.startswith('Digital Hash:'):
            # Check if hash is on the same line after "Digital Hash:"
            hash_part = line.replace('Digital Hash:', '').strip()
            if hash_part:
                digital_hash = hash_part
            else:
                # Hash is on the next line
                if i + 1 < len(lines):
                    digital_hash = lines[i + 1].strip()

    # If still not found, try simple colon-separated format
    if not cert_id and not digital_hash and ':' in qr_data:
        parts = qr_data.split(':', 1)
        if len(parts) == 2:
            cert_id = parts[0].strip()
            digital_hash = parts[1].strip()

    return cert_id, digital_hash
    print("DEBUG RAW QR:", repr(qr_data))


def verify_qr_authenticity(cert_id, digital_hash):
    """Verify if certificate ID and hash match database records"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM certificates 
        WHERE cert_id = ? AND digital_hash = ?
    """, (cert_id, digital_hash))

    result = cursor.fetchone()
    conn.close()

    return result is not None


def verify_certificate_qr(certificate_image, institution_code):
    """Complete QR verification workflow using OpenCV"""
    from .config import INSTITUTION_CONFIG

    config = INSTITUTION_CONFIG.get(institution_code)
    if not config or 'qr' not in config:
        return {"authentic": False, "error": "No QR configuration for institution"}

    # Extract QR region
    qr_region = extract_qr_region(certificate_image, config['qr']['roi'])

    # Read QR code
    qr_data = read_qr_code_opencv(qr_region)
    if not qr_data:
        return {"authentic": False, "error": "No QR code detected or unable to decode"}

    # DEBUG: Print what was read from QR
    print(f"DEBUG: Raw QR data: '{qr_data}'")

    # Parse QR data
    cert_id, digital_hash = parse_qr_data(qr_data)

    # DEBUG: Print parsing results
    print(f"DEBUG: Parsed cert_id: '{cert_id}'")
    print(f"DEBUG: Parsed digital_hash: '{digital_hash}'")

    if not cert_id:
        return {"authentic": False, "error": "Could not extract certificate ID from QR data", "qr_data": qr_data}

    if not digital_hash:
        return {"authentic": False, "error": "Could not extract digital hash from QR data", "qr_data": qr_data,
                "cert_id": cert_id}

    # Verify against database
    is_authentic = verify_qr_authenticity(cert_id, digital_hash)

    return {
        "authentic": is_authentic,
        "cert_id": cert_id,
        "digital_hash": digital_hash,  # Add this for debugging
        "qr_data": qr_data,
        "message": "QR verification successful" if is_authentic else "QR verification failed - certificate not found in database"
    }

