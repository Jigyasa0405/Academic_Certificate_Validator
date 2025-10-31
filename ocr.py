import pandas as pd
from PIL import Image
import pytesseract
import re
from fuzzywuzzy import fuzz

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


db = pd.read_csv("C:\Juhi laptop backup\JUHI\CODING RELATED (Projects and Documents)\SIH\EduCred_verify\EduCred-Verify\datasets\ocr_dataset.csv")

# Normalize text for fuzzy matching
def normalize(text):
    return re.sub(r'\s+', ' ', text).strip().upper()

def clean_name(name):
    # Remove common trailing phrases that are not part of name
    name = re.sub(r'\b(PRESENTED.*|For completing.*|In the year.*)$', '', name, flags=re.IGNORECASE)
    # Keep only alphabetic parts
    name = re.sub(r'[^A-Za-z\s]', '', name)
    return name.strip()
def extract_year(text, cert_no=None):
    clean_text = text
    if cert_no:
        clean_text = clean_text.replace(cert_no, "")  # remove cert no part

    # Look for year 19xx or 20xx
    match = re.search(r'\b(19|20)\d{2}\b', clean_text)
    if match:
        return match.group(0)
    return None

# Extract certificate info including year
def extract_certificate_info(img):
    text = pytesseract.image_to_string(img)
    info = {}

    # Certificate ID
    match = re.search(r'(JH[-_ ]?UNI[-_ ]?\d{4}[-_ ]?\d+)', text, re.IGNORECASE)
    if match:
        info["certificate_no"] = re.sub(r'[\s\-_]+', '-', match.group(1)).upper()

    # Institution
    match = re.search(r'(Ranchi Tech Institute|Jharkhand State University|Jharkhand Business School)', text, re.IGNORECASE)
    if match:
        info["institution"] = match.group(1).title()

    # Name + Course block
    # Name + Course block
    match = re.search(r'(?:awarded to|is given to|THIS CERTIFICATE IS GIVEN TO)\s*\n?([A-Za-z\s]+)', text,
                      re.IGNORECASE)
    if match:
        raw_name = re.sub(r'\s+', ' ', match.group(1)).strip()

        # If course is stuck to name, split it
        course_match = re.search(r'(BBA|M\.?Sc\s+[A-Za-z]+|BA\s+[A-Za-z]+)', raw_name, re.IGNORECASE)
        if course_match:
            info["course"] = course_match.group(1).strip()
            raw_name = raw_name.replace(info["course"], "").strip()

        info["name"] = clean_name(raw_name)

    # # Course (fallback if not caught above)
    # if "course" not in info:
    #     match = re.search(r'(BBA|M\.?Sc\s+[A-Za-z]+|BA\s+[A-Za-z]+)', text, re.IGNORECASE)
    #     if match:
    #         info["course"] = match.group(1).strip()

    # Year
    # Certificate No
    match = re.search(
        r'Cert(?:ificate)?\s*No[:\-\s]*([A-Z0-9\-]+)',
        text,
        re.IGNORECASE
    )
    if match:
        cert_no = match.group(1).strip()
        info["certificate_no"] = cert_no
    else:
        info["certificate_no"] = "-"

    # Year
    year = extract_year(text, cert_no)
    if year:
        info["year"] = year

    return info

# Fuzzy validation
def validate_certificate_fuzzy(info, db, threshold=90):
    for _, row in db.iterrows():
        score_cert = fuzz.ratio(normalize(info.get("certificate_no","")), normalize(row["certificate_no"]))
        score_name = fuzz.ratio(normalize(info.get("name","")), normalize(row["name"]))
        score_inst = fuzz.ratio(normalize(info.get("institution","")), normalize(row["institution"]))
        # score_course = fuzz.ratio(normalize(info.get("course","")), normalize(row["course"]))
        score_year = (info.get("year","") == str(row["year"]))

        if score_cert > threshold and score_name > threshold and score_inst > threshold  and score_year:
            return True, row.to_dict()
    return False, None

# Load image
img = Image.open("/Users/jigyasaverma/Desktop/backend/Edu_cred_verify/EduCred-Verify/datasets/certificates/RTI_014.png")
extracted_info = extract_certificate_info(img)
print("Extracted:", extracted_info)

# Validate
valid, record = validate_certificate_fuzzy(extracted_info, db)

if valid:
    print("✅ Certificate is VALID")
    print("Matched Record:", record)
else:
    print("❌ Certificate is INVALID")

