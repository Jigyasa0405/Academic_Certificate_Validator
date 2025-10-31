from fastapi import FastAPI, UploadFile, File, HTTPException
from .database import init_database, get_institution_assets
from .utils import get_institution_code_from_name
from .forgery_detection import verify_seal, verify_signature, extract_roi
import cv2
import os
import uvicorn

# Initialize the app
app = FastAPI(title="Academic Certificate Verifier")


# Initialize the database when the app starts
@app.on_event("startup")
def on_startup():
    init_database()
    print("Database initialized successfully!")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Points to /backend


@app.post("/verify")
async def verify_certificate_endpoint(
        file: UploadFile = File(...),
        institution: str = None,
        seal_roi: str = None,
        signature_roi: str = None
):
    """API endpoint to verify a certificate"""
    try:
        # Save uploaded file temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # TODO: Integrate OCR service
        ocr_data = {
            'institution': institution or 'Jharkhand State University',
        }

        img = cv2.imread(file_path)

        if seal_roi:
            seal_region = extract_roi(img, eval(seal_roi))
        else:
            seal_region = img

        if signature_roi:
            signature_region = extract_roi(img, eval(signature_roi))
        else:
            signature_region = img

        # Perform verification
        result = verify_certificate(ocr_data, seal_region, signature_region)

        os.remove(file_path)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")


def verify_certificate(ocr_data, extracted_seal_image, extracted_signature_image):
    """Main verification function"""
    institution_name = ocr_data.get('institution')
    institution_code = get_institution_code_from_name(institution_name)

    if not institution_code:
        return {
            "authentic": False,
            "error": f"Unknown institution: {institution_name}",
            "details": {
                "institution": institution_name,
                "seal_score": 0.0,
                "signature_score": 0.0
            }
        }

    assets = get_institution_assets(institution_code)
    if not assets:
        return {
            "authentic": False,
            "error": f"Institution assets not found for: {institution_code}",
            "details": {
                "institution": institution_name,
                "institution_code": institution_code,
                "seal_score": 0.0,
                "signature_score": 0.0
            }
        }

    ref_seal_path = os.path.join(BASE_DIR, assets['seal_path'])
    ref_signature_path = os.path.join(BASE_DIR, assets['signature_path'])

    ref_seal = cv2.imread(ref_seal_path, 0)
    ref_signature = cv2.imread(ref_signature_path, 0)

    if ref_seal is None:
        return {
            "authentic": False,
            "error": f"Reference seal not found at: {ref_seal_path}",
            "details": {
                "institution": institution_name,
                "institution_code": institution_code,
                "seal_score": 0.0,
                "signature_score": 0.0
            }
        }

    if ref_signature is None:
        return {
            "authentic": False,
            "error": f"Reference signature not found at: {ref_signature_path}",
            "details": {
                "institution": institution_name,
                "institution_code": institution_code,
                "seal_score": 0.0,
                "signature_score": 0.0
            }
        }

    seal_score = verify_seal(extracted_seal_image, ref_seal)
    signature_score = verify_signature(extracted_signature_image, ref_signature)

    seal_authentic = seal_score >= 0.3
    signature_authentic = signature_score >= 0.05
    overall_authentic = seal_authentic and signature_authentic

    return {
        "authentic": overall_authentic,
        "details": {
            "institution": institution_name,
            "institution_code": institution_code,
            "seal_score": round(seal_score, 3),
            "signature_score": round(signature_score, 3),
            "seal_authentic": seal_authentic,
            "signature_authentic": signature_authentic,
            "seal_threshold": 0.3,
            "signature_threshold": 0.05
        }
    }


@app.get("/")
async def root():
    return {"message": "Academic Certificate Verification API", "status": "active"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)