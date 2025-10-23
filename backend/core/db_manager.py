import sqlite3
import os
from typing import Optional, Dict, Any

# --- File Configuration ---

DB_NAME = "memorando_data.db"
DOC_STORAGE_DIR = "documents_json" 

# Default paths (used by the global instance)
DB_PATH = os.path.join(os.getcwd(), DB_NAME)
DOC_STORAGE_PATH = os.path.join(os.getcwd(), DOC_STORAGE_DIR)

class DBManager:
    """Centralized SQLite connection and schema manager."""
    
    def __init__(self):
        # Assign default global paths to instance variables if not set by a subclass (e.g., TestDBManager)
        if not hasattr(self, 'DB_PATH'):
            self.DB_PATH = DB_PATH
        if not hasattr(self, 'DOC_STORAGE_PATH'):
            self.DOC_STORAGE_PATH = DOC_STORAGE_PATH

        # Ensure the storage directory exists using the instance path
        self._ensure_storage_directory_exists()

    def _ensure_storage_directory_exists(self):
        """Creates the local directory for storing document JSON files if it doesn't exist."""
        if not os.path.exists(self.DOC_STORAGE_PATH):
            os.makedirs(self.DOC_STORAGE_PATH)
            print(f"📁 Storage directory created: {self.DOC_STORAGE_PATH}")
        else:
            print(f"📁 Storage directory already exists: {self.DOC_STORAGE_PATH}")


    def get_connection(self) -> sqlite3.Connection:
        """Returns a new database connection, using the instance path."""
        # CRITICAL FIX: Use self.DB_PATH to connect to the correct database (test or production)
        return sqlite3.connect(self.DB_PATH)

    def initialize_db(self):
        """Creates database tables if they do not exist."""
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
                json_file_path TEXT NOT NULL,
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
        
        # 4. Study Sessions Table 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                document_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                session_json_path TEXT NOT NULL, -- Ruta al archivo JSON de esta sesión
                segment_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (document_id) REFERENCES documents (id)
            );
        """)

        conn.commit()
        conn.close()
        print(f"✅ Database '{DB_NAME}' and tables initialized.")


# Single instantiation for production/development use
db_manager = DBManager()
