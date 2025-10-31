#config.py
INSTITUTION_CONFIG = {
    "JHAR": {
        "seal": {
            "roi":  [0.730, 0.050, 0.892, 0.249],
            "reference_image": "assets/seals/jhar_seal.png",  # Changed path
            "threshold": 0.25
        },
        "signature": {
            "roi":  [0.520, 0.791, 0.695, 0.899],
            "reference_image": "assets/signatures/jhar_signature.png",  # Changed path
            "threshold": 0.3
        }
    },
    "RANC": {
        "seal": {
            "roi": [0.426, 0.034, 0.573, 0.244],
            "reference_image": "assets/seals/ranc_seal.png",  # Changed path
            "threshold": 0.25
        },
        "signature": {
            "roi": [0.597, 0.759, 0.853, 0.838],
            "reference_image": "assets/signatures/ranc_signature.png",  # Changed path
            "threshold": 0.4
        }
    },
    "JHAR_BS": {
        "seal": {
            "roi":[0.397, 0.045, 0.612, 0.285],
            "reference_image": "assets/seals/jhar_bs_seal.png",  # Changed path
            "threshold": 0.25
        },
        "signature": {
            "roi": [0.732, 0.782, 0.889, 0.865],
            "reference_image": "assets/signatures/jhar_bs_signature.png",  # Changed path
            "threshold": 0.2
        }
    }
}

INSTITUTION_NAME_TO_CODE = {
    "Jharkhand State University": "JHAR",
    "Ranchi Tech Institute": "RANC",
    "Jharkhand Business School": "JHAR_BS"
}

OCR_INSTITUTION_MAPPING = {
    "jharkhand state university": "Jharkhand State University",
    "ranchi tech institute": "Ranchi Tech Institute",
    "jharkhand business school": "Jharkhand Business School",
    "jsu": "Jharkhand State University",
    "rti": "Ranchi Tech Institute",
    "jbs": "Jharkhand Business School"
}