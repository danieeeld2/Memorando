import bcrypt
import sqlite3
from typing import Dict, Any, Optional
from backend.core.db_manager import db_manager, DBManager 

# --- Hashing Utilities ---

def hash_password(password: str) -> str:
    """Hashes the password using bcrypt."""
    password_bytes = password.encode('utf-8')
    # Generate a salt and hash
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    # Decode to store as string
    return hashed.decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    """Verifies if the password matches the stored hash."""
    try:
        # bcrypt.checkpw requires bytes
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

# --- User Service ---

class UserService:
    """
    Business logic service for user management (Registration, Login).
    This class supports dependency injection of the DBManager for testing.
    """
    
    def __init__(self, db_manager: DBManager = db_manager):
        """
        Initializes the service with a DBManager instance.
        """
        self.db_manager = db_manager 

    def register_user(self, email: str, password: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Registers a new user, hashing the password.
        Returns the new user's data (id, email, name) or None on failure (e.g., email already exists).
        """
        password_hash = hash_password(password)
        
        # Use the injected db_manager instance
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
                (email, password_hash, name)
            )
            conn.commit()
            
            # Return the created user's data
            return {
                "user_id": cursor.lastrowid,
                "email": email,
                "name": name
            }
        except sqlite3.IntegrityError:
            print(f"❌ Error: Email '{email}' already exists.")
            return None
        finally:
            conn.close()

    def login_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Attempts to log in.
        Returns user data (without hash) if successful, or None on failure.
        """
        # Use the injected db_manager instance
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # 1. Find user by email
        cursor.execute("SELECT id, email, password_hash, name FROM users WHERE email = ?", (email,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            user_id, user_email, password_hash, user_name = user_data
            
            # 2. Verify password
            if check_password(password, password_hash):
                # Return the user data dict matching the API response model
                return {
                    "user_id": user_id,
                    "email": user_email,
                    "name": user_name
                }
            
        return None

# Single instantiation for production/development use
user_service = UserService()
