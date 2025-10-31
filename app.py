from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from PIL import Image
import pytesseract
import re
from fuzzywuzzy import fuzz
import cv2
import numpy as np
import os
from datetime import datetime
import tempfile
from forgery_detection import detect_forgery

app = Flask(__name__)
CORS(app)

# Load the database
db = pd.read_csv("C:\Juhi laptop backup\JUHI\CODING RELATED (Projects and Documents)\SIH\EduCred_verify\EduCred-Verify\datasets\ocr_dataset.csv")


def normalize(text):
    """Normalize text for fuzzy matching"""
    return re.sub(r'\s+', ' ', text).strip().upper()


def clean_name(name):
    """Clean extracted name"""
    # Remove common trailing phrases that are not part of name
    name = re.sub(r'\b(PRESENTED.*|For completing.*|In the year.*)$', '', name, flags=re.IGNORECASE)
    # Keep only alphabetic parts
    name = re.sub(r'[^A-Za-z\s]', '', name)
    return name.strip()


def extract_year(text, cert_no=None):
    """Extract year from text"""
    clean_text = text
    if cert_no:
        clean_text = clean_text.replace(cert_no, "")  # remove cert no part

    # Look for year 19xx or 20xx
    match = re.search(r'\b(19|20)\d{2}\b', clean_text)
    if match:
        return match.group(0)
    return None


def extract_certificate_info(img):
    """Extract certificate info including year"""
    text = pytesseract.image_to_string(img)
    info = {}

    # Certificate ID - Multiple patterns
    patterns = [
        r'(JH[-_ ]?UNI[-_ ]?\d{4}[-_ ]?\d+)',
        r'Cert(?:ificate)?\s*No[:\-\s]*([A-Z0-9\-]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if 'JH' in pattern:
                info["certificate_no"] = re.sub(r'[\s\-_]+', '-', match.group(1)).upper()
            else:
                info["certificate_no"] = match.group(1).strip()
            break

    if "certificate_no" not in info:
        info["certificate_no"] = "-"

    # Institution
    institutions = [
        'Ranchi Tech Institute',
        'Jharkhand State University',
        'Jharkhand Business School'
    ]

    for institution in institutions:
        if re.search(institution, text, re.IGNORECASE):
            info["institution"] = institution
            break

    # Name + Course block
    match = re.search(r'(?:awarded to|is given to|THIS CERTIFICATE IS GIVEN TO)\s*\n?([A-Za-z\s]+)', text,
                      re.IGNORECASE)
    if match:
        raw_name = re.sub(r'\s+', ' ', match.group(1)).strip()

        # If course is stuck to name, split it
        course_patterns = [r'(BBA|M\.?Sc\s+[A-Za-z]+|BA\s+[A-Za-z]+)', r'(Bachelor.*|Master.*|Diploma.*)']

        for course_pattern in course_patterns:
            course_match = re.search(course_pattern, raw_name, re.IGNORECASE)
            if course_match:
                info["course"] = course_match.group(1).strip()
                raw_name = raw_name.replace(info["course"], "").strip()
                break

        info["name"] = clean_name(raw_name)

    # Year extraction
    year = extract_year(text, info.get("certificate_no"))
    if year:
        info["year"] = year

    # Store raw text for debugging
    info["raw_text"] = text

    return info


def validate_certificate_fuzzy(info, db, threshold=85):
    """Validate certificate using fuzzy matching"""
    best_match = None
    best_scores = {}

    for _, row in db.iterrows():
        scores = {}
        scores['cert'] = fuzz.ratio(normalize(info.get("certificate_no", "")), normalize(str(row["certificate_no"])))
        scores['name'] = fuzz.ratio(normalize(info.get("name", "")), normalize(str(row["name"])))
        scores['inst'] = fuzz.ratio(normalize(info.get("institution", "")), normalize(str(row["institution"])))
        scores['year'] = 100 if info.get("year", "") == str(row["year"]) else 0

        # Calculate overall score
        overall_score = (scores['cert'] * 0.4 + scores['name'] * 0.3 + scores['inst'] * 0.2 + scores['year'] * 0.1)

        # Check if this is a good match
        if (scores['cert'] > threshold and scores['name'] > threshold and
                scores['inst'] > threshold and scores['year'] > 50):

            if best_match is None or overall_score > best_scores.get('overall', 0):
                best_match = row.to_dict()
                best_scores = scores
                best_scores['overall'] = overall_score

    return best_match is not None, best_match, best_scores


def parse_qr_data(qr_data):
    """Extract certificate ID and hash from QR data"""
    print(f"DEBUG: Raw QR data received: '{qr_data}'")
    print(f"DEBUG: QR data type: {type(qr_data)}")
    print(f"DEBUG: QR data length: {len(qr_data)}")
    
    lines = qr_data.strip().split('\n')
    print(f"DEBUG: Split into {len(lines)} lines: {lines}")
    
    cert_id = None
    digital_hash = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        print(f"DEBUG: Processing line {i}: '{line}'")
        
        # Look for certificate ID patterns
        if 'Certificate ID:' in line:
            cert_id = line.replace('Certificate ID:', '').strip()
            print(f"DEBUG: Found cert_id with 'Certificate ID:' pattern: '{cert_id}'")
        elif 'Cert ID:' in line:
            cert_id = line.replace('Cert ID:', '').strip()
            print(f"DEBUG: Found cert_id with 'Cert ID:' pattern: '{cert_id}'")
        elif 'ID:' in line:
            cert_id = line.replace('ID:', '').strip()
            print(f"DEBUG: Found cert_id with 'ID:' pattern: '{cert_id}'")
            
        # Look for digital hash
        elif 'Digital Hash:' in line:
            digital_hash = line.replace('Digital Hash:', '').strip()
            print(f"DEBUG: Found hash with 'Digital Hash:' pattern: '{digital_hash}'")
        elif 'Hash:' in line:
            digital_hash = line.replace('Hash:', '').strip()
            print(f"DEBUG: Found hash with 'Hash:' pattern: '{digital_hash}'")
    
    # If still no cert_id found, try to extract from the raw data using regex
    if not cert_id:
        print("DEBUG: No cert_id found with labels, trying regex patterns...")
        cert_patterns = [
            r'(JH[-_]?UNI[-_]?\d{4}[-_]?\d+)',
            r'(RTI[-_]?\d{4}[-_]?\d+)',
            r'([A-Z]{2,4}[-_]?\d{3,4})',
            r'([A-Z]+-[A-Z]+-\d{4}-\d+)'
        ]
        
        for pattern in cert_patterns:
            match = re.search(pattern, qr_data, re.IGNORECASE)
            if match:
                cert_id = match.group(1)
                print(f"DEBUG: Found cert_id with regex pattern '{pattern}': '{cert_id}'")
                break
    
    # If no hash found in labeled format, check if any line looks like a hash
    if not digital_hash:
        print("DEBUG: No hash found with labels, checking for hash-like strings...")
        for line in lines:
            line = line.strip()
            # Look for alphanumeric strings that could be hashes (at least 10 chars)
            if len(line) >= 10 and re.match(r'^[a-zA-Z0-9]+$', line) and line != cert_id:
                digital_hash = line
                print(f"DEBUG: Found potential hash: '{digital_hash}'")
                break
    
    print(f"DEBUG: Final results - cert_id: '{cert_id}', digital_hash: '{digital_hash}'")
    return cert_id, digital_hash


def verify_qr_authenticity(cert_id, digital_hash):
    """Verify if both certificate ID and hash match database records"""
    # Search in the actual CSV database
    matching_records = db[db['certificate_no'].str.contains(cert_id, case=False, na=False)]
    
    if matching_records.empty:
        return None  # Certificate ID not found
    
    # Get the first matching record
    record = matching_records.iloc[0]
    
    # Check if the record has a digital_hash column and if it matches
    if 'digital_hash' in record.index:
        stored_hash = str(record['digital_hash']).strip()
        if stored_hash == digital_hash:
            return record.to_dict()
    else:
        # If your CSV doesn't have a digital_hash column yet, you can use this fallback
        # For demonstration, let's create a simple hash verification
        print(f"Warning: digital_hash column not found in database")
        
        # Fallback: Create expected hashes for known certificates
        expected_hashes = {
            'JH-UNI-2018-201': 'abc123hash456def',
            'RTI-2019-305': 'xyz789hash123abc',
            # Add more certificates as needed
        }
        
        expected_hash = expected_hashes.get(cert_id)
        if expected_hash and expected_hash == digital_hash:
            return record.to_dict()
        
        return None
    
    # Certificate ID exists but hash doesn't match
    return None


@app.route('/api/verify-certificate', methods=['POST'])
def verify_certificate():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'tiff'}
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        if file_extension not in allowed_extensions:
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name

        try:
            # Load and process image
            img = Image.open(temp_path)

            # Extract information using OCR
            extracted_info = extract_certificate_info(img)

            # Validate against database
            is_valid, matched_record, confidence_scores = validate_certificate_fuzzy(extracted_info, db)

            # Perform REAL forgery detection using your actual implementation
            try:
                forgery_results = detect_forgery(temp_path, extracted_info, debug=False)
            except Exception as forgery_error:
                print(f"Forgery detection error: {forgery_error}")
                # Fallback if forgery detection fails
                forgery_results = {
                    'institution': extracted_info.get('institution', ''),
                    'institution_code': 'UNKNOWN',
                    'seal_match_score': 0.0,
                    'signature_match_score': 0.0,
                    'seal_authentic': False,
                    'signature_authentic': False,
                    'overall_authentic': False,
                    'error': str(forgery_error),
                    'thresholds': {
                        'seal': 0.25,
                        'signature': 0.05
                    }
                }

            # Prepare response
            response_data = {
                'success': True,
                'extracted_info': {
                    'certificate_no': matched_record['certificate_no'] if matched_record else extracted_info.get(
                        'certificate_no', 'Not found'),
                    'name': matched_record['name'] if matched_record else extracted_info.get('name', 'Not found'),
                    'institution': matched_record['institution'] if matched_record else extracted_info.get(
                        'institution', 'Not found'),
                    'course': matched_record.get('course', '') if matched_record else extracted_info.get('course',
                                                                                                         'Not found'),
                    'year': str(matched_record['year']) if matched_record else extracted_info.get('year', 'Not found'),
                    'raw_text': extracted_info.get('raw_text', ''),
                    'processing_timestamp': datetime.now().isoformat()
                },
                'validation': {
                    'is_valid': is_valid,
                    'status': 'VERIFIED' if is_valid else 'INVALID',
                    'overall_confidence': int(confidence_scores.get('overall', 0)) if confidence_scores else 0,
                    'confidence_scores': {
                        'ocr_quality': 98,  # You can calculate this based on OCR confidence
                        'name_match': confidence_scores.get('name', 0) if confidence_scores else 0,
                        'institution_match': confidence_scores.get('inst', 0) if confidence_scores else 0,
                        'certificate_format': confidence_scores.get('cert', 0) if confidence_scores else 0,
                        'seal_authentic': forgery_results['seal_authentic'],
                        'signature_authentic': forgery_results['signature_authentic']
                    },
                    'matched_record': matched_record if is_valid else None
                },
                'forgery_detection': forgery_results
            }

            return jsonify(response_data)

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scan-qr', methods=['POST'])
def scan_qr():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name

        try:
            # Load image
            img = cv2.imread(temp_path)
            if img is None:
                return jsonify({'success': False, 'error': 'Invalid image file'}), 400

            # Decode QR code
            detector = cv2.QRCodeDetector()
            data, vertices_array, binary_qr = detector.detectAndDecode(img)
            
            print(f"DEBUG: QR detection result - data: '{data}', vertices found: {vertices_array is not None}")
            
            if not data:
                return jsonify({'success': False, 'error': 'No QR code detected in image'}), 400

            # Parse QR data to extract certificate ID and hash
            cert_id, digital_hash = parse_qr_data(data)
            
            if not cert_id:
                return jsonify({
                    'success': False, 
                    'error': f'Could not extract certificate ID from QR code. QR contains: "{data}"',
                    'qr_data': data
                }), 400

            if not digital_hash:
                return jsonify({
                    'success': False, 
                    'error': f'Could not extract digital hash from QR code. Found cert_id: {cert_id}',
                    'qr_data': data,
                    'cert_id': cert_id
                }), 400

            print(f"DEBUG: Extracted cert_id: '{cert_id}', hash: '{digital_hash}'")

            # Verify against database
            matching_record = verify_qr_authenticity(cert_id, digital_hash)
            
            if not matching_record:
                # Check if cert_id exists but hash doesn't match
                cert_exists = db[db['certificate_no'].str.contains(cert_id, case=False, na=False)]
                if not cert_exists.empty:
                    return jsonify({
                        'success': False, 
                        'error': 'Certificate ID found but digital hash does not match. This QR code may be forged.',
                        'qr_data': data,
                        'cert_id': cert_id,
                        'hash_provided': digital_hash,
                        'status': 'FORGED'
                    }), 400
                else:
                    return jsonify({
                        'success': False, 
                        'error': f'Certificate ID "{cert_id}" not found in database',
                        'qr_data': data,
                        'cert_id': cert_id,
                        'status': 'NOT_FOUND'
                    }), 404

            return jsonify({
                'success': True,
                'data': {
                    'documentType': 'Digital Certificate',
                    'name': matching_record['name'],
                    'certificateId': matching_record['certificate_no'],
                    'institution': matching_record['institution'],
                    'course': matching_record.get('course', ''),
                    'year': str(matching_record['year']),
                    'status': 'Valid',
                    'qr_raw_data': data,
                    'digital_hash': digital_hash,
                    'verification_method': 'QR Code + Database Hash Match'
                }
            })

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        print(f"ERROR in scan_qr: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Certificate verification API is running'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)