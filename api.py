# backend/app/api.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import datetime

from ocr import extract_certificate_info, validate_certificate_fuzzy
from forgery import detect_forgery

import pandas as pd

app = FastAPI()

# CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load DB
DB_PATH = "/Users/jigyasaverma/Desktop/backend/Edu_cred_verify/EduCred-Verify/datasets/ocr_dataset.csv"
db = pd.read_csv(DB_PATH)

@app.post("/api/verify-certificate")
async def verify_certificate(file: UploadFile = File(...)):
    try:
        # 1️⃣ Read uploaded image
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))

        # 2️⃣ OCR extraction
        extracted_info = extract_certificate_info(img)
        extracted_info["processing_timestamp"] = datetime.datetime.now().isoformat()

        # 3️⃣ OCR / DB fuzzy validation
        valid_ocr, matched_record = validate_certificate_fuzzy(extracted_info, db)

        ocr_result = {
            "is_valid": valid_ocr,
            "status": "VERIFIED" if valid_ocr else "INVALID",
            "confidence_scores": {},  # optional: you can expand per-field scores
            "matched_record": matched_record,
        }

        # 4️⃣ Forgery detection
        # Save temp file for OpenCV
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(contents)

        forgery_result = detect_forgery(temp_path, extracted_info, debug=False)

        # 5️⃣ Combine results
        return {
            "success": True,
            "extracted_info": extracted_info,
            "ocr_validation": ocr_result,
            "forgery_validation": forgery_result,
            "validation": {
                "is_valid": valid_ocr and forgery_result['overall_authentic'],
                "status": "VERIFIED" if valid_ocr and forgery_result['overall_authentic'] else "INVALID",
                "overall_confidence": None,  # you can calculate combined %
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
