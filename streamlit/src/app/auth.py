"""
Authentication module for Streamlit app
Uses the same authentication logic as FastAPI backend
"""
import streamlit as st
import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
import sys

# Import db_utils from FastAPI app (same database and functions)
# Try multiple import paths to handle different execution contexts
import sqlite3
import bcrypt

_db_utils_imported = False
try:
    # Try importing from fastapi app (when running in Docker or with proper PYTHONPATH)
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    from fastapi.src.app.db_utils import get_user, verify_password
    _db_utils_imported = True
except ImportError:
    try:
        # Try alternative path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
        from fastapi.src.app.db_utils import get_user, verify_password
        _db_utils_imported = True
    except ImportError:
        pass

# Fallback: implement directly if import failed
if not _db_utils_imported:
    DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/metadata.db")
    
    def get_conn():
        return sqlite3.connect(DB_PATH)
    
    def get_user(username: str):
        """Get user from database"""
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, username, password_hash FROM admin_users WHERE username = ?", (username,))
            row = cur.fetchone()
            if row:
                return {"id": row[0], "username": row[1], "password_hash": row[2]}
        return None
    
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), hashed.encode())

# JWT Configuration (same as FastAPI)
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create JWT access token (same as FastAPI)"""
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict | None:
    """Verify JWT token and return payload if valid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def login_user(username: str, password: str) -> tuple[bool, str | None]:
    """
    Authenticate user and return (success, token)
    Same logic as FastAPI /login endpoint
    """
    user = get_user(username)
    if not user or not verify_password(password, user["password_hash"]):
        return False, None
    
    access_token = create_access_token(data={"sub": user["username"]})
    return True, access_token

def is_authenticated() -> bool:
    """Check if user is authenticated based on session state"""
    if 'access_token' not in st.session_state:
        return False
    
    token = st.session_state.access_token
    payload = verify_token(token)
    return payload is not None

def require_auth():
    """
    Require authentication for a page.
    If not authenticated, show login page and stop execution.
    Call this at the top of any page that needs authentication.
    """
    if not is_authenticated():
        render_login_page()
        st.stop()

def render_login_page():
    """Render login page for admin authentication"""
    st.markdown("""
        <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
            <h1 style='color: white; margin: 0; text-align: center;'>🔐 Admin Login</h1>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=False):
        st.markdown("### Please enter your credentials")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit_button = st.form_submit_button("Login", use_container_width=True)
        
        if submit_button:
            if not username or not password:
                st.error("⚠️ Please enter both username and password")
            else:
                # Strip whitespace from inputs
                username = username.strip()
                password = password.strip()
                
                success, token = login_user(username, password)
                if success and token:
                    st.session_state.access_token = token
                    st.session_state.username = username
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
                    # Debug info (remove in production)
                    user = get_user(username)
                    if user:
                        st.caption(f"💡 User '{username}' exists. Please check your password.")
                    else:
                        st.caption(f"💡 User '{username}' not found.")
    
    st.markdown("---")
    st.info("💡 This is an admin-only area. Please contact your administrator if you need access.")

