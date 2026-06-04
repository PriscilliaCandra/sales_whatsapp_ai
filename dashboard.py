# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import requests
import time
import re
from config import ACCESS_TOKEN, PHONE_NUMBER_ID
from database import save_admin_message, update_daily_stats

# Konfigurasi halaman
st.set_page_config(
    page_title="Indotrading AI Sales Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ AMBIL KONFIGURASI ============
WHATSAPP_API_URL = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

# ============ CUSTOM CSS ============
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
    
    .stApp {
        background-color: #F8F8F8;
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E2E2;
    }
    
    .sidebar-brand {
        padding: 18px 20px 16px;
        border-bottom: 1px solid #F0F0F0;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    
    .sidebar-logo {
        width: 32px;
        height: 32px;
        background: #C8102E;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        font-size: 14px;
    }
    
    .sidebar-name {
        font-size: 14px;
        font-weight: 600;
        color: #222222;
    }
    
    .sidebar-name small {
        display: block;
        font-size: 10px;
        font-weight: 400;
        color: #9A9A9A;
        letter-spacing: 0.4px;
    }
    
    .menu-section {
        padding: 14px 12px 4px;
        font-size: 10px;
        font-weight: 600;
        color: #9A9A9A;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }
    
    .metric-card {
        background-color: white;
        border: 1px solid #E2E2E2;
        border-radius: 10px;
        padding: 14px 16px;
        transition: all 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    .metric-card.accent {
        border-left: 3px solid #C8102E;
    }
    
    .metric-label {
        font-size: 11px;
        color: #9A9A9A;
        font-weight: 500;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    .metric-value {
        font-size: 22px;
        font-weight: 700;
        color: #222222;
        line-height: 1;
        margin-bottom: 5px;
    }
    
    .metric-change {
        font-size: 11px;
        display: flex;
        align-items: center;
        gap: 3px;
    }
    
    .metric-change.up {
        color: #1A7A4A;
    }
    
    .metric-change.down {
        color: #C8102E;
    }
    
    .badge-ai {
        background-color: #FCEAED;
        color: #C8102E;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-admin {
        background-color: #E3F2FD;
        color: #1976D2;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 600;
        display: inline-block;
    }
    
    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        display: inline-block;
    }
    
    .status-online {
        background-color: #1A7A4A;
    }
    
    .agent-card {
        background-color: white;
        border: 1px solid #E2E2E2;
        border-radius: 10px;
        padding: 12px 14px;
    }
    
    .agent-name {
        font-size: 12px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .agent-stat {
        font-size: 10px;
        color: #9A9A9A;
    }
    
    .progress-bar {
        height: 4px;
        background-color: #E2E2E2;
        border-radius: 2px;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 2px;
    }
    
    .progress-fill.red {
        background-color: #C8102E;
    }
    
    .progress-fill.green {
        background-color: #1A7A4A;
    }
    
    .divider {
        border-top: 1px solid #E2E2E2;
        margin: 12px 0;
    }
    
    .icon-red {
        color: #C8102E;
    }
    
    .fa, .fas, .far, .fab {
        margin-right: 4px;
    }
    
    /* Avatar styling */
    .avatar-customer {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background-color: #C8102E;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    
    .avatar-ai {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background-color: #FCEAED;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    
    .avatar-admin {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background-color: #E3F2FD;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    
    /* Tabel permission */
    .perm-table { width: 100%; border-collapse: collapse; }
    .perm-table th { text-align: left; padding: 10px; background: #F8F8F8; border-bottom: 1px solid #E2E2E2; }
    .perm-table td { padding: 8px 10px; border-bottom: 1px solid #F0F0F0; }
</style>
""", unsafe_allow_html=True)

# ============ FUNGSI DATABASE ============
@st.cache_data(ttl=30)
def load_conversations():
    try:
        conn = sqlite3.connect('chat_history.db')
        df = pd.read_sql_query("SELECT * FROM conversations ORDER BY created_at DESC", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error load conversations: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_stats():
    df = load_conversations()
    if df.empty:
        return {'total': 0, 'ai_handled': 0, 'admin_sent': 0, 'unique_customers': 0, 'today': 0}
    
    today = datetime.now().date()
    today_count = len(df[pd.to_datetime(df['created_at']).dt.date == today])
    
    return {
        'total': len(df),
        'ai_handled': len(df[df['status'] == 'handled_by_ai']),
        'admin_sent': len(df[df['status'] == 'admin_sent']),
        'unique_customers': df['customer_phone'].nunique(),
        'today': today_count
    }

def load_contacts():
    df = load_conversations()
    if df.empty:
        return pd.DataFrame()
    
    contacts = df.groupby(['customer_phone', 'customer_name', 'customer_company']).agg({
        'created_at': 'max',
        'message': 'last',
        'reply': 'last'
    }).reset_index()
    
    contacts.columns = ['phone', 'name', 'company', 'last_chat', 'last_message', 'last_reply']
    contacts['last_chat'] = pd.to_datetime(contacts['last_chat'])
    contacts = contacts.sort_values('last_chat', ascending=False)
    
    msg_count = df.groupby('customer_phone').size().reset_index(name='message_count')
    msg_count.columns = ['phone', 'message_count']
    contacts = contacts.merge(msg_count, on='phone', how='left')
    
    return contacts

def get_chat_history(phone):
    df = load_conversations()
    if df.empty:
        return pd.DataFrame()
    return df[df['customer_phone'] == phone].sort_values('created_at', ascending=True)

def format_phone_number(nomor):
    nomor = str(nomor).strip().replace("+", "").replace(" ", "").replace("-", "")
    if nomor.startswith("0"):
        nomor = "62" + nomor[1:]
    elif not nomor.startswith("62"):
        nomor = "62" + nomor
    return nomor

def send_whatsapp_message(to_number, message):
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        return False, "Token atau Phone Number ID tidak ditemukan"
    
    to_number = format_phone_number(to_number)
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            save_admin_message(to_number, message)
            st.cache_data.clear()
            return True, "Pesan berhasil dikirim"
        else:
            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
            return False, f"API Error: {error_msg}"
    except requests.exceptions.Timeout:
        return False, "Timeout: Server tidak merespon"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-logo">IT</div>
        <div class="sidebar-name">Indotrading AI<br><small>Admin Dashboard</small></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="menu-section">MENU UTAMA</div>', unsafe_allow_html=True)
    
    menu = st.radio(
        "Menu Utama",
        ["Overview", "AI Inbox", "AI Outbound", "Contacts", "Analytics", "User Management", "Campaign", "Templates", "Recipient Lists"],
        format_func=lambda x: x,
        label_visibility="collapsed",
        index=0
    )
    
    st.markdown('<div class="menu-section">KONFIGURASI</div>', unsafe_allow_html=True)
    
    stats = load_stats()
    st.markdown(f"""
    <div style="background-color: #F8F8F8; border-radius: 8px; padding: 12px; margin-top: 10px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-size: 11px; color: #9A9A9A;"><i class="fas fa-comments"></i> Total Chat</span>
            <span style="font-size: 14px; font-weight: 600; color: #C8102E;">{stats['total']}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="font-size: 11px; color: #9A9A9A;"><i class="fas fa-robot"></i> AI Handled</span>
            <span style="font-size: 14px; font-weight: 600;">{stats['ai_handled']}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="font-size: 11px; color: #9A9A9A;"><i class="fas fa-user-shield"></i> Admin Sent</span>
            <span style="font-size: 14px; font-weight: 600;">{stats['admin_sent']}</span>
        </div>
        <div class="divider"></div>
        <div style="font-size: 10px; color: #9A9A9A; text-align: center;">
            <i class="far fa-clock"></i> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============ OVERVIEW ============
if menu == "Overview":
    stats = load_stats()
    df = load_conversations()
    contacts = load_contacts()
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
            <h2 style="margin: 0; color: #222222;">Overview</h2>
            <p style="margin: 5px 0 0 0; color: #9A9A9A; font-size: 12px;">— {datetime.now().strftime('%A, %d %B %Y')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    persen_ai = round((stats['ai_handled'] / stats['total'] * 100) if stats['total'] > 0 else 0)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card accent">
            <div class="metric-label"><i class="fas fa-comments"></i> Total Percakapan</div>
            <div class="metric-value">{stats['total']:,}</div>
            <div class="metric-change up"><i class="fas fa-arrow-up"></i> +18% vs minggu lalu</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label"><i class="fas fa-robot"></i> Ditangani AI</div>
            <div class="metric-value">{persen_ai}%</div>
            <div class="metric-change up"><i class="fas fa-arrow-up"></i> +4% vs minggu lalu</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label"><i class="fas fa-stopwatch"></i> Waktu Respons</div>
            <div class="metric-value">2.4<span style="font-size:13px"> dtk</span></div>
            <div class="metric-change up"><i class="fas fa-arrow-down"></i> -0.8 dtk lebih cepat</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label"><i class="fas fa-users"></i> Customer Unik</div>
            <div class="metric-value">{stats['unique_customers']}</div>
            <div class="metric-change up"><i class="fas fa-arrow-up"></i> +23% vs minggu lalu</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Volume Percakapan")
        if not df.empty:
            df['date'] = pd.to_datetime(df['created_at']).dt.date
            daily = df.groupby('date').size().reset_index(name='count')
            daily = daily.tail(7)
            fig = px.bar(daily, x='date', y='count', color_discrete_sequence=['#C8102E'])
            fig.update_layout(plot_bgcolor='white', height=300, margin=dict(l=20, r=20, t=30, b=20))
            fig.update_traces(marker=dict(cornerradius=4))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada data")
    
    with col_chart2:
        st.subheader("Conversion Rate")
        if not df.empty:
            daily_rate = df.groupby('date').size().reset_index(name='count')
            daily_rate = daily_rate.tail(7)
            daily_rate['rate'] = daily_rate['count'] * 2
            fig = px.line(daily_rate, x='date', y='rate', markers=True, color_discrete_sequence=['#C8102E'])
            fig.update_layout(plot_bgcolor='white', height=300, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada data")
    
    st.markdown("### Percakapan Terbaru")
    if not contacts.empty:
        display_df = contacts.head(10).copy()
        display_df['Kontak'] = display_df['name']
        display_df['Pesan Terakhir'] = display_df['last_message'].str[:60] + '...' if display_df['last_message'].str.len().max() > 60 else display_df['last_message']
        display_df['Channel'] = 'WhatsApp'
        display_df['Ditangani'] = 'AI Agent'
        display_df['Status'] = 'Aktif'
        
        st.dataframe(
            display_df[['Kontak', 'Pesan Terakhir', 'Channel', 'Ditangani', 'Status']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Kontak": st.column_config.TextColumn("Kontak", width="medium"),
                "Pesan Terakhir": st.column_config.TextColumn("Pesan Terakhir", width="large"),
                "Channel": st.column_config.TextColumn("Channel", width="small"),
                "Ditangani": st.column_config.TextColumn("Ditangani", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
            }
        )
    else:
        st.info("Belum ada percakapan")

# ============ AI INBOX ============
elif menu == "AI Inbox":
    st.markdown("<h2><i class='fas fa-inbox'></i> AI Inbox</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9A9A9A; margin-bottom: 20px;'>— Kelola percakapan dengan customer secara real-time</p>", unsafe_allow_html=True)
    
    contacts = load_contacts()
    
    if not contacts.empty:
        contacts = contacts.drop_duplicates(subset=['phone'])
        
        search = st.text_input("Cari kontak...", placeholder="Nama atau nomor", key="search_inbox")
        
        filtered = contacts
        if search:
            filtered = contacts[
                contacts['name'].str.contains(search, case=False, na=False) |
                contacts['phone'].str.contains(search, case=False, na=False)
            ]
        
        if 'selected_contact_inbox' not in st.session_state:
            st.session_state.selected_contact_inbox = filtered.iloc[0]['phone'] if len(filtered) > 0 else None
        
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.markdown("##### Kontak")
            
            for _, contact in filtered.iterrows():
                initials = contact['name'][:2].upper() if contact['name'] else "??"
                msg_count = contact.get('message_count', 0)
                last_time = pd.to_datetime(contact['last_chat']).strftime('%H:%M') if contact['last_chat'] else '-'
                preview = str(contact['last_message'])[:35] + "..." if len(str(contact['last_message'])) > 35 else str(contact['last_message'])
                
                is_selected = st.session_state.selected_contact_inbox == contact['phone']
                button_label = f"{initials} | {contact['name']}  ({msg_count})  •  {last_time}\n{preview}"
                
                btn_type = "primary" if is_selected else "secondary"
                
                if st.button(button_label, key=f"inbox_btn_{contact['phone']}", use_container_width=True, type=btn_type):
                    st.session_state.selected_contact_inbox = contact['phone']
                    st.rerun()
        
        with col_right:
            selected = contacts[contacts['phone'] == st.session_state.selected_contact_inbox]
            if not selected.empty:
                selected = selected.iloc[0]
                
                st.markdown(f"""
                <div style="background-color: #FCEAED; padding: 12px 16px; border-radius: 10px; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 40px; height: 40px; border-radius: 50%; background-color: #C8102E; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold;">{selected['name'][:2].upper()}</div>
                        <div>
                            <div style="font-weight: 600;">{selected['name']}</div>
                            <div style="font-size: 11px; color: #1A7A4A;"><i class="fas fa-circle" style="font-size: 8px;"></i> Online</div>
                        </div>
                        <div style="margin-left: auto;">
                            <span style="background-color: #C8102E; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px;"><i class="fas fa-robot"></i> AI Agent</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                chat_history = get_chat_history(st.session_state.selected_contact_inbox)
                chat_container = st.container(height=350)
                
                with chat_container:
                    for _, msg in chat_history.iterrows():
                        time_str = pd.to_datetime(msg['created_at']).strftime('%H:%M')
                        
                        # PESAN DARI CUSTOMER (kiri dengan avatar)
                        if msg['direction'] == 'incoming' or (msg['status'] == 'handled_by_ai' and not msg['reply']):
                            st.markdown(f"""
                            <div style="display: flex; align-items: flex-start; gap: 10px; margin-bottom: 16px;">
                                <div class="avatar-customer">
                                    <i class="fas fa-user" style="color: white; font-size: 14px;"></i>
                                </div>
                                <div style="max-width: 70%;">
                                    <div style="background-color: #C8102E; color: white; padding: 10px 14px; border-radius: 18px; border-bottom-left-radius: 4px;">
                                        {msg['message']}
                                    </div>
                                    <div style="font-size: 10px; color: #999; margin-top: 4px;">
                                        <i class="far fa-clock"></i> {time_str}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # BALASAN AI (kanan dengan avatar AI)
                        if msg['reply'] and msg['status'] == 'handled_by_ai':
                            st.markdown(f"""
                            <div style="display: flex; align-items: flex-start; justify-content: flex-end; gap: 10px; margin-bottom: 16px;">
                                <div style="max-width: 70%; text-align: right;">
                                    <div style="background-color: #F0F0F0; color: #222; padding: 10px 14px; border-radius: 18px; border-bottom-right-radius: 4px;">
                                        {msg['reply']}
                                    </div>
                                    <div style="font-size: 10px; color: #999; margin-top: 4px;">
                                        <i class="far fa-clock"></i> {time_str} • AI
                                    </div>
                                </div>
                                <div class="avatar-ai">
                                    <i class="fas fa-robot" style="color: #C8102E; font-size: 14px;"></i>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # PESAN ADMIN (kanan dengan avatar admin)
                        if msg['status'] == 'admin_sent' and msg['direction'] == 'outgoing':
                            st.markdown(f"""
                            <div style="display: flex; align-items: flex-start; justify-content: flex-end; gap: 10px; margin-bottom: 16px;">
                                <div style="max-width: 70%; text-align: right;">
                                    <div style="background-color: #1976D2; color: white; padding: 10px 14px; border-radius: 18px; border-bottom-right-radius: 4px;">
                                        {msg['message']}
                                    </div>
                                    <div style="font-size: 10px; color: #999; margin-top: 4px;">
                                        <i class="far fa-clock"></i> {time_str} • Admin
                                    </div>
                                </div>
                                <div class="avatar-admin">
                                    <i class="fas fa-user-shield" style="color: #1976D2; font-size: 14px;"></i>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # FORM KIRIM PESAN
                st.markdown('<div style="border-top: 1px solid #E2E2E2; padding: 12px; background: white; border-radius: 0 0 10px 10px;">', unsafe_allow_html=True)
                
                with st.form(key="send_message_form", clear_on_submit=True):
                    col_input, col_btn = st.columns([4, 1])
                    
                    with col_input:
                        user_message = st.text_input(
                            "Pesan",
                            placeholder="Ketik pesan... (akan dikirim ke WhatsApp customer)",
                            label_visibility="collapsed",
                            key="human_message"
                        )
                    
                    with col_btn:
                        submitted = st.form_submit_button("Kirim", use_container_width=True, type="primary")
                    
                    if submitted and user_message:
                        to_number = selected['phone']
                        
                        with st.spinner("Mengirim pesan..."):
                            success, result = send_whatsapp_message(to_number, user_message)
                            
                            if success:
                                st.success("Pesan terkirim!")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Gagal mengirim: {result}")
                    elif submitted and not user_message:
                        st.warning("Silakan ketik pesan terlebih dahulu")
                
                st.markdown("""
                <div style="font-size: 10px; color: #999; text-align: center; margin-top: 8px;">
                    <i class="fas fa-info-circle"></i> Pesan akan dikirim langsung ke WhatsApp customer. AI tetap akan merespon otomatis jika customer membalas.
                </div>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                st.info("Pilih kontak dari daftar di sebelah kiri")
    else:
        st.info("Belum ada kontak. Customer akan muncul saat chat pertama!")

# ============ AI OUTBOUND ============
elif menu == "AI Outbound":
    st.markdown("<h2><i class='fas fa-bullhorn'></i> AI Outbound</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9A9A9A; margin-bottom: 20px;'>— Kirim pesan massal ke customer</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label"><i class="fas fa-broadcast-tower"></i> Total Broadcast</div>
            <div class="metric-value">24</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label"><i class="fas fa-envelope-open-text"></i> Open Rate</div>
            <div class="metric-value">78%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("Buat Broadcast Baru")
    
    with st.form("broadcast_form"):
        template_name = st.text_input("Nama Template", placeholder="Promo Ramadhan 2025")
        message = st.text_area("Pesan", height=150, placeholder="Masukkan pesan broadcast...")
        col_file, col_schedule = st.columns(2)
        with col_file:
            file = st.file_uploader("Upload CSV Customer", type=['csv'])
        with col_schedule:
            schedule = st.selectbox("Jadwalkan", ["Kirim Sekarang", "Senin 10:00", "Selasa 14:00", "Rabu 09:00"])
        if st.form_submit_button("Kirim Broadcast", use_container_width=True):
            if message:
                st.success(f"Broadcast '{template_name}' berhasil dijadwalkan!")
            else:
                st.error("Harap isi pesan broadcast")

# ============ CONTACTS ============
elif menu == "Contacts":
    st.markdown("<h2><i class='fas fa-address-book'></i> Contacts / Leads</h2>", unsafe_allow_html=True)
    contacts = load_contacts()
    if not contacts.empty:
        st.dataframe(contacts[['name', 'phone', 'company', 'message_count', 'last_chat']], use_container_width=True)
        csv = contacts.to_csv(index=False).encode('utf-8')
        st.download_button("Export ke CSV", csv, "contacts_export.csv", "text/csv")
    else:
        st.info("Belum ada kontak")

# ============ ANALYTICS ============
elif menu == "Analytics":
    st.markdown("<h2><i class='fas fa-chart-line'></i> Analytics</h2>", unsafe_allow_html=True)
    df = load_conversations()
    if not df.empty:
        st.subheader("Tren Percakapan")
        df['date'] = pd.to_datetime(df['created_at']).dt.date
        daily = df.groupby('date').size().reset_index(name='count')
        fig = px.line(daily, x='date', y='count', markers=True, color_discrete_sequence=['#C8102E'])
        fig.update_layout(plot_bgcolor='white', height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Jam Sibuk Percakapan")
        df['hour'] = pd.to_datetime(df['created_at']).dt.hour
        hourly = df.groupby('hour').size().reset_index(name='count')
        fig = px.bar(hourly, x='hour', y='count', color_discrete_sequence=['#C8102E'])
        fig.update_layout(plot_bgcolor='white', height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Top Customer Paling Aktif")
        top = df['customer_name'].value_counts().head(10).reset_index()
        top.columns = ['Customer', 'Jumlah']
        fig = px.bar(top, x='Customer', y='Jumlah', color_discrete_sequence=['#C8102E'])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Belum ada data analitik")

# ============ USER MANAGEMENT ============
elif menu == "User Management":
    st.markdown("<h2><i class='fas fa-users'></i> User Management</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9A9A9A; margin-bottom: 20px;'>— Kelola user, role, dan akses sistem</p>", unsafe_allow_html=True)
    
    from database import get_users
    
    tab_users, tab_add_user, tab_roles = st.tabs(["Daftar User", "Tambah User", "Role Management"])
    
    with tab_users:
        users = get_users()
        if users:
            display_users = []
            for u in users:
                display_users.append({
                    "ID": u['id'],
                    "Username": u['username'],
                    "Email": u['email'],
                    "Phone": u['phone'],
                    "Role": "Supervisor" if u['role'] == 'supervisor' else "Agent",
                    "Status": "Active" if u['is_active'] else "Inactive"
                })
            st.dataframe(display_users, use_container_width=True)
        else:
            st.info("Belum ada user")
    
    with tab_add_user:
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Username")
                email = st.text_input("Email")
                phone = st.text_input("Nomor WhatsApp")
            with col2:
                role = st.selectbox("Role", ["agent", "supervisor"])
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Konfirmasi Password", type="password")
            
            if st.form_submit_button("Tambah User", use_container_width=True):
                if password == confirm_password:
                    st.success(f"User {username} berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.error("Password tidak cocok")
    
    with tab_roles:
        st.subheader("Role & Permission")
        
        st.markdown("""
        <table class="perm-table">
            <tr><th>Fitur</th><th>Supervisor</th><th>Agent</th></tr>
            <tr><td>Dashboard Overview</td><td><i class="fas fa-check-circle" style="color: #1A7A4A;"></i></td><td><i class="fas fa-check-circle" style="color: #1A7A4A;"></i></td></tr>
            <tr><td>AI Inbox</td><td><i class="fas fa-check-circle" style="color: #1A7A4A;"></i></td><td><i class="fas fa-check-circle" style="color: #1A7A4A;"></i></td></tr>
            <tr><td>Kirim Pesan Manual</td><td><i class="fas fa-check-circle" style="color: #1A7A4A;"></i></td><td><i class="fas fa-check-circle" style="color: #1A7A4A;"></i></td></tr>
            <tr><td>Assign Chat ke Agent</td><td><i class="fas fa-check-circle" style="color: #1A7A4A;"></i></td><td><i class="fas fa-times-circle" style="color: #C8102E;"></i></td></tr>
            <tr><td>Broadcast Campaign</td><td><i class="fas fa-check-circle" style="color: #1A7A4A;"></i></td><td><i class="fas fa-times-circle" style="color: #C8102E;"></i></td></tr>
            <tr><td>Buat Template</td><td><i class="fas fa-check-circle" style="color: #1A7A4A;"></i></td><td><i class="fas fa-times-circle" style="color: #C8102E;"></i></td></tr>
            <tr><td>Upload Recipient List</td><td><i class="fas fa-check-circle" style="color: #1A7A4A;"></i></td><td><i class="fas fa-times-circle" style="color: #C8102E;"></i></td></tr>
            <tr><td>Kelola User</td><td><i class="fas fa-check-circle" style="color: #1A7A4A;"></i></td><td><i class="fas fa-times-circle" style="color: #C8102E;"></i></td></tr>
        </table>
        """, unsafe_allow_html=True)

# ============ CAMPAIGN ============
elif menu == "Campaign":
    st.markdown("<h2><i class='fas fa-bullhorn'></i> Campaign Management</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9A9A9A; margin-bottom: 20px;'>— Buat dan kelola campaign broadcast</p>", unsafe_allow_html=True)
    
    from database import get_campaigns, create_campaign, get_templates, get_recipient_lists, send_broadcast_campaign
    
    tab_campaigns, tab_create = st.tabs(["Daftar Campaign", "Buat Campaign Baru"])
    
    with tab_campaigns:
        campaigns = get_campaigns()
        if campaigns:
            # Header tabel
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1.5, 1, 1, 0.8, 0.6])
            with col1: st.markdown("**Nama Campaign**")
            with col2: st.markdown("**Template**")
            with col3: st.markdown("**Kategori**")
            with col4: st.markdown("**Status**")
            with col5: st.markdown("**Terkirim**")
            with col6: st.markdown("**Aksi**")
            st.divider()
            
            for c in campaigns:
                col1, col2, col3, col4, col5, col6 = st.columns([2, 1.5, 1, 1, 0.8, 0.6])
                
                with col1:
                    st.write(c['name'])
                with col2:
                    st.write(c['template_name'])
                with col3:
                    st.write(c['category'])
                with col4:
                    # Status dengan icon
                    if c['status'] == 'completed':
                        status_display = '<i class="fas fa-check-circle" style="color: #1A7A4A;"></i> Completed'
                    elif c['status'] == 'scheduled':
                        status_display = '<i class="fas fa-calendar-alt" style="color: #D97706;"></i> Scheduled'
                    elif c['status'] == 'draft':
                        status_display = '<i class="fas fa-pen-alt" style="color: #9A9A9A;"></i> Draft'
                    else:
                        status_display = f'<i class="fas fa-times-circle" style="color: #C8102E;"></i> {c["status"]}'
                    st.markdown(status_display, unsafe_allow_html=True)
                with col5:
                    st.write(f"{c.get('sent_count', 0)}/{c.get('total_recipients', 0)}")
                with col6:
                    if c['status'] in ['draft', 'scheduled']:
                        if st.button("Kirim", key=f"send_campaign_{c['id']}", use_container_width=False):
                            with st.spinner("Mengirim campaign..."):
                                success, message = send_broadcast_campaign(c['id'])
                                if success:
                                    st.success(f"✅ {message}")
                                    st.cache_data.clear()
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                    else:
                        st.button("✅", key=f"disabled_btn_{c['id']}", disabled=True, use_container_width=False)
                
                st.divider()
        else:
            st.info("Belum ada campaign. Buat campaign baru di tab sebelah kanan!")
    
    with tab_create:
        with st.form("create_campaign_form"):
            campaign_name = st.text_input("Nama Campaign", placeholder="Contoh: Promo Ramadhan 2025")
            
            col1, col2 = st.columns(2)
            with col1:
                templates = get_templates()
                template_options = [t['name'] for t in templates] if templates else []
                template_name = st.selectbox("Pilih Template", template_options if template_options else ["Belum ada template"])
            
            with col2:
                recipient_lists = get_recipient_lists()
                list_options = [l['name'] for l in recipient_lists] if recipient_lists else ["Belum ada recipient list"]
                recipient_list = st.selectbox("Pilih Recipient List", list_options if list_options else ["Belum ada list"])
            
            schedule_date = st.date_input("Jadwalkan", value=datetime.now().date())
            schedule_time = st.time_input("Waktu", value=datetime.now().time())
            
            if st.form_submit_button("Buat Campaign", use_container_width=True):
                if campaign_name and template_name != "Belum ada template" and recipient_list != "Belum ada recipient list":
                    campaign_data = {
                        'name': campaign_name,
                        'template_name': template_name,
                        'category': "Marketing",
                        'recipient_list': recipient_list,
                        'total_recipients': 0,
                        'created_by': 1,
                        'scheduled_at': f"{schedule_date} {schedule_time}"
                    }
                    
                    try:
                        create_campaign(campaign_data)
                        st.success(f"Campaign '{campaign_name}' berhasil dibuat!")
                        st.cache_data.clear()
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal membuat campaign: {e}")
                else:
                    if not campaign_name:
                        st.error("Nama campaign wajib diisi")
                    elif template_name == "Belum ada template":
                        st.error("Belum ada template. Buat template dulu di menu Templates")
                    elif recipient_list == "Belum ada recipient list":
                        st.error("Belum ada recipient list. Upload recipient list dulu di menu Recipient Lists")
                        
# ============ TEMPLATES ============
elif menu == "Templates":
    st.markdown("<h2><i class='fas fa-file-alt'></i> Message Templates</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9A9A9A; margin-bottom: 20px;'>— Buat dan kelola template pesan</p>", unsafe_allow_html=True)
    
    from database import get_templates, create_template
    
    tab_templates, tab_create = st.tabs(["Daftar Template", "Buat Template Baru"])
    
    with tab_templates:
        templates = get_templates()
        if templates:
            display_templates = []
            for t in templates:
                display_templates.append({
                    "Nama Template": t['name'],
                    "Tipe": t.get('type', '-'),
                    "Kategori": t.get('category', '-'),
                    "Status": "Approved" if t.get('status') == 'approved' else "Draft",
                    "Bahasa": t.get('language', 'id').upper(),
                    "Dibuat Oleh": t.get('creator', '-')
                })
            st.dataframe(display_templates, use_container_width=True)
        else:
            st.info("Belum ada template. Buat template baru di tab sebelah kanan!")
    
    with tab_create:
        with st.form("create_template_form"):
            template_name = st.text_input("Nama Template", placeholder="Contoh: welcome_message")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                template_type = st.selectbox("Tipe", ["Campaign", "Follow up", "Authentication"])
            with col2:
                template_category = st.selectbox("Kategori", ["Marketing", "Utility", "Authentication"])
            with col3:
                language = st.selectbox("Bahasa", ["id", "en", "ms"])
            
            header = st.text_input("Header (opsional)", placeholder="Contoh: Halo {{1}}")
            content = st.text_area("Isi Pesan", height=150, placeholder="Contoh: Selamat datang {{1}} di Indotrading...")
            footer = st.text_input("Footer (opsional)", placeholder="Contoh: Terima kasih")
            
            if st.form_submit_button("Simpan Template", use_container_width=True):
                if template_name and content:
                    template_data = {
                        'name': template_name,
                        'type': template_type,
                        'category': template_category,
                        'language': language,
                        'content': content,
                        'header': header,
                        'footer': footer,
                        'created_by': 1
                    }
                    
                    try:
                        create_template(template_data)
                        st.success(f"Template '{template_name}' berhasil disimpan!")
                        st.cache_data.clear()
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan template: {e}")
                else:
                    st.error("Nama template dan isi pesan wajib diisi")

# ============ RECIPIENT LISTS ============
elif menu == "Recipient Lists":
    st.markdown("<h2><i class='fas fa-list'></i> Recipient Lists</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9A9A9A; margin-bottom: 20px;'>— Kelola daftar penerima broadcast</p>", unsafe_allow_html=True)
    
    from database import get_recipient_lists, create_recipient_list
    import os
    import csv
    
    # Buat folder uploads jika belum ada
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    tab_lists, tab_upload = st.tabs(["Daftar Recipient", "Upload File"])
    
    with tab_lists:
        lists = get_recipient_lists()
        if lists:
            display_lists = []
            for l in lists:
                display_lists.append({
                    "Nama List": l['name'],
                    "Channel": l['channel'],
                    "Kontak": l['contacts_count'],
                    "Status": "Completed" if l['upload_status'] == 'completed' else "⏳ Processing",
                    "Sumber": l.get('source', '-'),
                    "Tanggal": l['created_at'][:10] if l['created_at'] else '-'
                })
            st.dataframe(display_lists, use_container_width=True)
        else:
            st.info("Belum ada recipient list")
    
    with tab_upload:
        with st.form("upload_recipient_form", clear_on_submit=True):
            list_name = st.text_input("Nama List", placeholder="Contoh: Customer Promo Ramadhan")
            
            col1, col2 = st.columns(2)
            with col1:
                channel = st.selectbox("Channel", ["WhatsApp", "SMS", "Email"])
            with col2:
                source = st.selectbox("Sumber", ["File upload", "CSV import", "Spreadsheet sync"])
            
            uploaded_file = st.file_uploader("Upload File", type=['csv', 'xlsx', 'txt'])
            
            if st.form_submit_button("Upload & Proses", use_container_width=True):
                if list_name and uploaded_file:
                    # SIMPAN FILE KE DISK DENGAN PATH LENGKAP
                    file_extension = uploaded_file.name.split('.')[-1]
                    saved_filename = f"uploads/{list_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
                    
                    with open(saved_filename, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Hitung jumlah kontak di file
                    contacts_count = 0
                    try:
                        with open(saved_filename, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                contacts_count += 1
                    except Exception as e:
                        st.warning(f"File terupload, tapi tidak bisa membaca jumlah kontak: {e}")
                    
                    recipient_data = {
                        'name': list_name,
                        'channel': channel,
                        'contacts_count': contacts_count,
                        'upload_status': 'completed',
                        'source': source,
                        'file_path': saved_filename,  
                        'created_by': 1
                    }
                    
                    try:
                        create_recipient_list(recipient_data)
                        st.success(f"List '{list_name}' berhasil diupload! ({contacts_count} kontak)")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal upload: {e}")
                else:
                    st.error("Nama list dan file wajib diisi")