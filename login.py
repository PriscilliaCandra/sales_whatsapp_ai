# login.py
import streamlit as st
from auth import authenticate_user, register_user

def show_login():
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 30px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .login-header {
        text-align: center;
        margin-bottom: 30px;
    }
    .login-logo {
        width: 60px;
        height: 60px;
        background: #C8102E;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 15px;
        color: white;
        font-size: 24px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Hapus query parameters yang mungkin tersisa
    st.query_params.clear()
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Masukkan username")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            
            if st.form_submit_button("Login", use_container_width=True, type="primary"):
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user_name = user['username']
                        st.session_state.user_role = user['role']
                        
                        # Simpan ke localStorage via JavaScript
                        st.markdown(f"""
                        <script>
                            localStorage.setItem("auth", "true");
                            localStorage.setItem("user", "{user['username']}");
                            localStorage.setItem("role", "{user['role']}");
                            window.location.href = window.location.pathname + "?auth=true&user={user['username']}&role={user['role']}";
                        </script>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Username atau password salah")
                else:
                    st.warning("Harap isi username dan password")
    
    with tab2:
        with st.form("register_form"):
            reg_username = st.text_input("Username", placeholder="Buat username", key="reg_username")
            reg_email = st.text_input("Email", placeholder="email@example.com")
            reg_phone = st.text_input("Nomor WhatsApp", placeholder="628xxxxxxxxxx")
            reg_password = st.text_input("Password", type="password", placeholder="Buat password", key="reg_password")
            reg_confirm = st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password")
            
            if st.form_submit_button("Daftar", use_container_width=True):
                if reg_username and reg_email and reg_phone and reg_password:
                    if reg_password == reg_confirm:
                        success, result = register_user(
                            reg_username, reg_email, reg_phone, 'agent', reg_password, 1
                        )
                        if success:
                            st.success("Pendaftaran berhasil! Silakan login.")
                        else:
                            st.error(f"Gagal mendaftar: {result}")
                    else:
                        st.error("Password tidak cocok")
                else:
                    st.warning("Harap isi semua field")

def show_logout():
    with st.sidebar:
        st.markdown("---")
        
        st.markdown(f"""
        <div style="background-color: #F8F8F8; border-radius: 8px; padding: 10px; margin-bottom: 10px; text-align: center;">
            <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                <i class="fas fa-user-circle" style="color: #C8102E; font-size: 20px;"></i>
                <div>
                    <div style="font-size: 13px; font-weight: 600; color: #222;">
                        {st.session_state.get('user_name', 'Guest')}
                    </div>
                    <div style="font-size: 10px; color: #999;">
                        {st.session_state.get('user_role', 'Unknown')}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Logout", use_container_width=True):
            # Clear session state
            for key in ['authenticated', 'user_id', 'user_name', 'user_email', 'user_phone', 'user_role']:
                if key in st.session_state:
                    del st.session_state[key]
            # Clear query parameters
            st.query_params.clear()
            st.rerun()