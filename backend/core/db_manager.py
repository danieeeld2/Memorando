import sqlite3
import os
import json
from typing import Optional, Dict, Any

# --- File Configuration ---

DB_NAME = "memorando_data.db"
DOC_STORAGE_DIR = "documents_json" 

# Default paths
DB_PATH = os.path.join(os.getcwd(), DB_NAME)
DOC_STORAGE_PATH = os.path.join(os.getcwd(), DOC_STORAGE_DIR)

class DBManager:
    """Centralized SQLite connection and schema manager."""
    
    def __init__(self):
        if not hasattr(self, 'DB_PATH'):
            self.DB_PATH = DB_PATH
        if not hasattr(self, 'DOC_STORAGE_PATH'):
            self.DOC_STORAGE_PATH = DOC_STORAGE_PATH

        self._ensure_storage_directory_exists()

    def _ensure_storage_directory_exists(self):
        """Creates the local directory for storing document JSON files."""
        if not os.path.exists(self.DOC_STORAGE_PATH):
            os.makedirs(self.DOC_STORAGE_PATH)
            print(f"📁 Storage directory created: {self.DOC_STORAGE_PATH}")
        else:
            print(f"📁 Storage directory already exists: {self.DOC_STORAGE_PATH}")


    def get_connection(self) -> sqlite3.Connection:
        """Returns a new database connection."""
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
                session_json_path TEXT NOT NULL,
                segment_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (document_id) REFERENCES documents (id)
            );
        """)

        conn.commit()
        conn.close()
        print(f"✅ Database '{DB_NAME}' and tables initialized.")


    def save_document_json(self, user_id: int, title: str, json_data: Dict[str, Any]) -> int | None:
        """
        Saves the structured JSON data to a local file and registers the document
        in the 'documents' table.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 1. Primero obtener el próximo ID (sin insertar todavía)
            cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM documents")
            document_id = cursor.fetchone()[0]
            
            if not document_id:
                raise sqlite3.Error("Failed to generate document ID.")

            # 2. Definir la ruta del archivo JSON
            json_filename = f"doc_{document_id}.json"
            json_file_path = os.path.join(self.DOC_STORAGE_PATH, json_filename)

            # 3. Insertar el documento con la ruta correcta directamente
            cursor.execute(
                "INSERT INTO documents (id, user_id, title, json_file_path) VALUES (?, ?, ?, ?)",
                (document_id, user_id, title, json_file_path)
            )

            # 4. Guardar el JSON en el sistema de archivos
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            
            conn.commit()
            print(f"✅ Document saved successfully. ID: {document_id}, Path: {json_file_path}")
            return document_id

        except sqlite3.Error as e:
            print(f"❌ DB Error saving document: {e}")
            conn.rollback()
            return None
        except Exception as e:
            print(f"❌ File System Error saving document JSON: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()


# Single instantiation
db_manager = DBManager()
