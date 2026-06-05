# auth.py
import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

DB_PATH = "chat_history.db"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, email, phone, role, is_active FROM users WHERE username = ? AND password_hash = ?",
        (username, hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()
    
    if user and user[5] == 1:
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'phone': user[3],
            'role': user[4],
            'is_active': user[5]
        }
    return None

def register_user(username, email, phone, role, password, created_by):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, email, phone, password_hash, role, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, phone, hash_password(password), role, created_by, datetime.now()))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return True, user_id
    except sqlite3.IntegrityError as e:
        conn.close()
        return False, str(e)

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, phone, role, is_active FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'phone': user[3],
            'role': user[4],
            'is_active': user[5]
        }
    return None

def update_user_status(user_id, is_active):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (is_active, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, phone, role, is_active, created_at FROM users ORDER BY id")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

def delete_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ? AND username != 'admin'", (user_id,))
    conn.commit()
    conn.close()

def get_agents():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, phone, email FROM users WHERE role = 'agent' AND is_active = 1")
    agents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return agents

def is_supervisor():
    return st.session_state.get('user_role') == 'supervisor'

def is_authenticated():
    return st.session_state.get('authenticated', False)

def login_required():
    if not is_authenticated():
        st.warning("Silakan login terlebih dahulu")
        st.stop()