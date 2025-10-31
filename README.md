# 🎓 Academic Validator - AI-Powered Certificate Verification System

![Academic Validator](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![React](https://img.shields.io/badge/React-18+-61DAFB)
![Flask](https://img.shields.io/badge/Flask-2.0+-black)
![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-green)

**Academic Validator** is an advanced AI-powered system designed to detect forged academic certificates and verify their authenticity using OCR, computer vision, and database validation. Built for educational institutions, employers, and verification agencies to combat credential fraud.

---

## 🌟 Key Features

### 🔍 **Intelligent OCR Analysis**
- Extracts certificate information including name, institution, certificate ID, course, and year
- Uses Tesseract OCR with fuzzy matching algorithms for robust text extraction
- Handles various certificate formats and layouts

### 🤖 **AI-Powered Forgery Detection**
- **Seal Verification**: Uses ORB (Oriented FAST and Rotated BRIEF) feature detection to compare institutional seals
- **Signature Matching**: Template matching algorithms verify signature authenticity
- **ROI Analysis**: Extracts and analyzes specific regions of interest from certificates

### 📊 **Database Validation**
- Cross-references extracted data against authorized certificate records
- Fuzzy matching with configurable confidence thresholds
- Comprehensive validation scoring system

### 📱 **QR Code Verification**
- Scans and decodes QR codes embedded in digital certificates
- Validates certificate ID and cryptographic hash against database
- Detects forged or tampered QR codes

### 💡 **Modern Web Interface**
- Beautiful, responsive React frontend with gradient animations
- Real-time processing status updates
- Detailed verification results with confidence scores
- Separate pages for document upload and QR scanning

---

## 🏗️ System Architecture

```
Academic_Validator/
├── backend/
│   ├── app/
│   │   ├── app.py                    # Flask API server
│   │   ├── config.py                 # Institution configurations & ROI coordinates
│   │   ├── forgery_detection.py     # Seal & signature verification
│   │   ├── database.py               # Database operations
│   │   ├── ocr.py                    # OCR processing module
│   │   └── qr_verification.py       # QR code validation
│   ├── assets/
│   │   ├── seals/                   # Reference seal images
│   │   └── signatures/              # Reference signature images
│   ├── datasets/
│   │   └── ocr_dataset.csv          # Certificate database
│   └── test_certificates/           # Sample certificates for testing
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Home.jsx              # Landing page
    │   │   ├── Verify.jsx            # Document verification page
    │   │   └── QRScanPage.jsx        # QR code scanning page
    │   └── components/
    │       └── ui/                   # Reusable UI components
    └── public/
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **Tesseract OCR** installed on your system

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/Academic_Validator.git
cd Academic_Validator/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install Tesseract OCR**
   - **Windows**: Download from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - **Linux**: `sudo apt-get install tesseract-ocr`
   - **Mac**: `brew install tesseract`

5. **Initialize database and assets**
```bash
python setup.py
```

6. **Configure institution settings**
   - Edit `app/config.py` to add your institution details
   - Add reference seal and signature images to `assets/` folders
   - Update ROI coordinates for your certificate layouts

7. **Run the Flask server**
```bash
cd app
python app.py
```
Server will start on `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd ../frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```
Frontend will start on `http://localhost:5173`

---

## 📖 Usage

### 1. Certificate Verification

**Upload a certificate image** → System performs:
- OCR text extraction
- Database validation
- Forgery detection (seal & signature)
- Comprehensive confidence scoring

**Results include:**
- ✅ Certificate details (ID, name, institution, course, year)
- 📊 Confidence scores for each validation component
- 🔬 Forgery detection results
- ✓ Overall authenticity status

### 2. QR Code Verification

**Upload QR code image** → System:
- Decodes QR data
- Extracts certificate ID and cryptographic hash
- Validates against database records
- Detects forged or invalid QR codes

### 3. API Endpoints

#### Verify Certificate
```http
POST /api/verify-certificate
Content-Type: multipart/form-data

Response:
{
  "success": true,
  "extracted_info": { ... },
  "validation": { ... },
  "forgery_detection": { ... }
}
```

#### Scan QR Code
```http
POST /api/scan-qr
Content-Type: multipart/form-data

Response:
{
  "success": true,
  "data": { ... }
}
```

#### Health Check
```http
GET /api/health

Response:
{
  "status": "healthy",
  "message": "Certificate verification API is running"
}
```

---

## 🔧 Configuration

### Adding New Institutions

Edit `backend/app/config.py`:

```python
INSTITUTION_CONFIG = {
    "YOUR_CODE": {
        "seal": {
            "roi": [x1, y1, x2, y2],  # Normalized coordinates
            "reference_image": "assets/seals/your_seal.png",
            "threshold": 0.25
        },
        "signature": {
            "roi": [x1, y1, x2, y2],
            "reference_image": "assets/signatures/your_sig.png",
            "threshold": 0.05
        }
    }
}
```

### Extracting Reference Images

Use the provided extraction script:
```bash
python extract_reference_images.py
```

This extracts seal and signature regions from legitimate certificates.

---

## 🧪 Testing

### Run Forgery Detection Tests
```bash
python test_forgery.py
```

### Debug Forgery Detection
```bash
python debug_forgery_test.py
```

### Test with Real Certificates
```bash
python test_real_certificate.py
```

---

## 🛠️ Technology Stack

### Backend
- **Flask**: RESTful API framework
- **OpenCV**: Computer vision and image processing
- **Tesseract OCR**: Text extraction
- **Pandas**: Data manipulation
- **FuzzyWuzzy**: Fuzzy string matching
- **Pillow**: Image handling

### Frontend
- **React 18**: UI framework
- **React Router**: Navigation
- **Tailwind CSS**: Styling
- **Lucide React**: Icons
- **Vite**: Build tool

### AI/ML Components
- **ORB Feature Detection**: Seal verification
- **Template Matching**: Signature verification
- **Fuzzy Matching**: Text validation
- **QR Code Detection**: Digital certificate validation

---

## 📊 Confidence Scoring

The system calculates multiple confidence scores:

- **OCR Quality**: Text extraction reliability (0-100%)
- **Name Match**: Fuzzy match score with database (0-100%)
- **Institution Match**: Institution name accuracy (0-100%)
- **Certificate Format**: ID format validation (0-100%)
- **Seal Authenticity**: Visual seal matching (0-100%)
- **Signature Authenticity**: Signature verification (0-100%)

**Overall Confidence**: Weighted average of all scores

---

## 🔒 Security Features

- ✅ File type validation (JPG, PNG, TIFF only)
- ✅ File size limits (10MB max)
- ✅ Temporary file cleanup
- ✅ CORS protection
- ✅ Database query sanitization
- ✅ Cryptographic hash validation for QR codes

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: Forgery detection returns 0% scores
- **Solution**: Ensure reference images are extracted from actual certificates
- Run `python debug_forgery_test.py` to diagnose
- Check ROI coordinates in `config.py`

**Issue**: OCR not extracting text properly
- **Solution**: Verify Tesseract installation
- Check image quality and resolution
- Update OCR patterns in `extract_certificate_info()`

**Issue**: Database connection errors
- **Solution**: Run `python setup.py` to initialize database
- Check CSV file path in `app.py`

**Issue**: QR code not detected
- **Solution**: Ensure QR code is clear and high resolution
- Test QR format matches expected pattern

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

---

## 🙏 Acknowledgments

- Tesseract OCR for text extraction capabilities
- OpenCV community for computer vision tools
- Flask and React communities for excellent frameworks
- All contributors who help improve this project

---

## 📧 Contact

For questions or support:
- **Email**: your.email@example.com
- **GitHub Issues**: [Create an issue](https://github.com/yourusername/Academic_Validator/issues)
- **LinkedIn**: [Your LinkedIn](https://linkedin.com/in/yourprofile)

---

## 🔮 Future Enhancements

- [ ] Blockchain integration for immutable certificate records
- [ ] Machine learning model for advanced forgery detection
- [ ] Multi-language OCR support
- [ ] Mobile application (iOS/Android)
- [ ] Real-time verification API for third-party integrations
- [ ] Advanced analytics dashboard
- [ ] Batch certificate verification
- [ ] Digital certificate issuance system

---

## ⭐ Show Your Support

Give a ⭐️ if this project helped you!

---

<div align="center">

**Built with ❤️ to fight credential fraud and protect academic integrity**

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-blue)](https://python.org)
[![Made with React](https://img.shields.io/badge/Made%20with-React-61DAFB)](https://reactjs.org)
[![Powered by AI](https://img.shields.io/badge/Powered%20by-AI-orange)](https://github.com/yourusername/Academic_Validator)

</div>
