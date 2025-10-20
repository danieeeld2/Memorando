import sqlite3
import os

# --- File Configuration ---

# Database file name
DB_NAME = "memorando_data.db"
# Directory where extracted JSON files will be stored
DOC_STORAGE_DIR = "documents_json" 

# Full paths
DB_PATH = os.path.join(os.getcwd(), DB_NAME)
DOC_STORAGE_PATH = os.path.join(os.getcwd(), DOC_STORAGE_DIR)

class DBManager:
    """
    Centralized SQLite connection and schema manager.
    """
    
    def __init__(self):
        # Ensure the storage directory exists when the manager is instantiated
        self._ensure_storage_directory_exists()

    def _ensure_storage_directory_exists(self):
        """
        Creates the local directory for storing document JSON files if it doesn't exist.
        """
        if not os.path.exists(DOC_STORAGE_PATH):
            os.makedirs(DOC_STORAGE_PATH)
            print(f"📁 Storage directory created: {DOC_STORAGE_PATH}")
        else:
            print(f"📁 Storage directory already exists: {DOC_STORAGE_PATH}")


    def get_connection(self):
        """Returns a new database connection."""
        return sqlite3.connect(DB_PATH)

    def initialize_db(self):
        """
        Creates database tables if they do not exist.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. Documents Table (stores metadata and JSON file path)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                json_file_path TEXT NOT NULL, -- PATH TO THE EXTRACTED JSON FILE
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)
        
        # 3. Study Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                document_id INTEGER,
                method_used TEXT NOT NULL,
                duration_minutes REAL NOT NULL,
                segments_completed INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (document_id) REFERENCES documents (id)
            );
        """)

        conn.commit()
        conn.close()
        print(f"✅ Database '{DB_NAME}' and tables initialized.")


# Single instantiation
db_manager = DBManager()
