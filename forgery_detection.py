# forgery detection
import cv2
import numpy as np
from database import get_institution_assets  
from config import INSTITUTION_CONFIG, INSTITUTION_NAME_TO_CODE, OCR_INSTITUTION_MAPPING
import os


def extract_roi(image, roi_ratio):
    height, width = image.shape[:2]
    x_start = int(roi_ratio[0] * width)
    y_start = int(roi_ratio[1] * height)
    x_end = int(roi_ratio[2] * width)
    y_end = int(roi_ratio[3] * height)
    return image[y_start:y_end, x_start:x_end]


def get_institution_code_from_ocr(ocr_institution_name):
    cleaned_name = ocr_institution_name.lower().strip()
    standard_name = OCR_INSTITUTION_MAPPING.get(cleaned_name, cleaned_name)
    return INSTITUTION_NAME_TO_CODE.get(standard_name)


def verify_seal(extracted_seal, reference_seal):
    if len(extracted_seal.shape) == 3:
        extracted_seal = cv2.cvtColor(extracted_seal, cv2.COLOR_BGR2GRAY)
    if len(reference_seal.shape) == 3:
        reference_seal = cv2.cvtColor(reference_seal, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(extracted_seal, None)
    kp2, des2 = orb.detectAndCompute(reference_seal, None)

    if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
        return 0.0

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    if len(matches) > 10:
        match_score = len(matches) / min(len(des1), len(des2))
        return min(match_score, 1.0)
    return 0.0


def verify_signature(extracted_signature, reference_signature):
    if len(extracted_signature.shape) == 3:
        extracted_gray = cv2.cvtColor(extracted_signature, cv2.COLOR_BGR2GRAY)
    else:
        extracted_gray = extracted_signature

    if len(reference_signature.shape) == 3:
        reference_gray = cv2.cvtColor(reference_signature, cv2.COLOR_BGR2GRAY)
    else:
        reference_gray = reference_signature

    ref_resized = cv2.resize(reference_gray, (extracted_gray.shape[1], extracted_gray.shape[0]))

    result = cv2.matchTemplate(extracted_gray, ref_resized, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)

    return max_val


def detect_forgery(certificate_path, ocr_data, debug=False):
    cert_img = cv2.imread(certificate_path)
    if cert_img is None:
        raise ValueError(f"Certificate image not found at: {certificate_path}")

    institution_name = ocr_data.get('institution', '')
    institution_code = get_institution_code_from_ocr(institution_name)

    if not institution_code:
        raise ValueError(f"Could not determine institution code from: {institution_name}")

    config = INSTITUTION_CONFIG.get(institution_code)
    if not config:
        raise ValueError(f"No configuration found for institution: {institution_code}")

    assets = get_institution_assets(institution_code)
    if not assets:
        raise ValueError(f"No assets found for institution: {institution_code}")

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ref_seal_path = os.path.join(base_dir, assets['seal_path'])
    ref_signature_path = os.path.join(base_dir, assets['signature_path'])

    ref_seal = cv2.imread(ref_seal_path)
    ref_signature = cv2.imread(ref_signature_path)

    if ref_seal is None:
        raise ValueError(f"Reference seal not found at: {ref_seal_path}")
    if ref_signature is None:
        raise ValueError(f"Reference signature not found at: {ref_signature_path}")

    seal_region = extract_roi(cert_img, config['seal']['roi'])
    signature_region = extract_roi(cert_img, config['signature']['roi'])

    if debug:
        cv2.imwrite(f"extracted_seal_{institution_code}.jpg", seal_region)
        cv2.imwrite(f"extracted_signature_{institution_code}.jpg", signature_region)

    seal_score = verify_seal(seal_region, ref_seal)
    signature_score = verify_signature(signature_region, ref_signature)

    seal_threshold = config['seal'].get('threshold', 0.25)
    signature_threshold = config['signature'].get('threshold', 0.05)

    return {
        'institution': institution_name,
        'institution_code': institution_code,
        'seal_match_score': round(seal_score, 2),
        'signature_match_score': round(signature_score, 3),
        'seal_authentic': seal_score >= seal_threshold,
        'signature_authentic': signature_score >= signature_threshold,
        'overall_authentic': seal_score >= seal_threshold and signature_score >= signature_threshold,
        'thresholds': {
            'seal': seal_threshold,
            'signature': signature_threshold
        }
    }