# database.py
import sqlite3
import os
import pandas as pd
from config import INSTITUTION_CONFIG

# Define database path relative to current file
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'certificate_database.db')

def get_db_connection():
    """Get database connection with proper error handling"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database with proper error handling"""
    try:
        conn = get_db_connection()
        if not conn:
            print("Failed to connect to database")
            return False
            
        cursor = conn.cursor()

        # Create institutions table
        create_institutions_table = """
        CREATE TABLE IF NOT EXISTS institutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            seal_image_path TEXT NOT NULL,
            signature_image_path TEXT NOT NULL
        );
        """
        cursor.execute(create_institutions_table)

        # Create certificates table for QR verification
        create_certificates_table = """
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cert_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            institution TEXT NOT NULL,
            course TEXT,
            year INTEGER,
            digital_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_certificates_table)

        # Insert institution data
        institutions_data = [
            ('JHAR', 'Jharkhand State University', 'assets/seals/jhar_seal.png', 'assets/signatures/jhar_signature.png'),
            ('RANC', 'Ranchi Tech Institute', 'assets/seals/ranc_seal.png', 'assets/signatures/ranc_signature.png'),
            ('JHAR_BS', 'Jharkhand Business School', 'assets/seals/jhar_bs_seal.png', 'assets/signatures/jhar_bs_signature.png')
        ]

        insert_institution_sql = """
        INSERT OR IGNORE INTO institutions (code, name, seal_image_path, signature_image_path)
        VALUES (?, ?, ?, ?);
        """
        cursor.executemany(insert_institution_sql, institutions_data)

        # Insert sample certificate data with hashes
        sample_certificates = [
            ('JH-UNI-2018-201', 'Akash Rana', 'Jharkhand State University', 'Computer Science', 2018, 'abc123hash456def'),
            ('RTI-2019-305', 'Priya Sharma', 'Ranchi Tech Institute', 'Electrical Engineering', 2019, 'xyz789hash123abc'),
            ('JBS-2020-101', 'Amit Verma', 'Jharkhand Business School', 'Business Administration', 2020, 'def456hash789abc')
        ]

        insert_cert_sql = """
        INSERT OR IGNORE INTO certificates (cert_id, name, institution, course, year, digital_hash)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        cursor.executemany(insert_cert_sql, sample_certificates)

        conn.commit()
        conn.close()
        print("Database initialized successfully!")
        return True
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def get_institution_assets(institution_code):
    """Get institution assets with fallback to config"""
    try:
        conn = get_db_connection()
        if not conn:
            # Fallback to config
            return get_assets_from_config(institution_code)
            
        cursor = conn.cursor()
        cursor.execute("SELECT seal_image_path, signature_image_path FROM institutions WHERE code = ?", (institution_code,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {"seal_path": result['seal_image_path'], "signature_path": result['signature_image_path']}
        else:
            # Fallback to config
            return get_assets_from_config(institution_code)
            
    except Exception as e:
        print(f"Error getting institution assets: {e}")
        # Fallback to config
        return get_assets_from_config(institution_code)

def get_assets_from_config(institution_code):
    """Fallback method to get assets from config"""
    if institution_code in INSTITUTION_CONFIG:
        config = INSTITUTION_CONFIG[institution_code]
        return {
            "seal_path": config['seal']['reference_image'],
            "signature_path": config['signature']['reference_image']
        }
    return None

def create_csv_fallback():
    """Create a CSV fallback if database fails"""
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'datasets', 'ocr_dataset.csv')
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        data = {
            'certificate_no': ['JH-UNI-2018-201', 'RTI-2019-305', 'JBS-2020-101'],
            'name': ['Akash Rana', 'Priya Sharma', 'Amit Verma'],
            'institution': ['Jharkhand State University', 'Ranchi Tech Institute', 'Jharkhand Business School'],
            'course': ['Computer Science', 'Electrical Engineering', 'Business Administration'],
            'year': [2018, 2019, 2020]
        }
        
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        print(f"CSV fallback created at: {csv_path}")
        return True
        
    except Exception as e:
        print(f"Error creating CSV fallback: {e}")
        return False

# Initialize database on import
if __name__ == "__main__":
    init_database()
    create_csv_fallback()