# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3

# Konfigurasi halaman
st.set_page_config(
    page_title="WhatsApp AI Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 WhatsApp AI Dashboard")
st.markdown("---")

# Koneksi database
def get_db_connection():
    return sqlite3.connect('chat_history.db')

# Load data
@st.cache_data(ttl=60)
def load_conversations():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM conversations ORDER BY created_at DESC", conn)
    conn.close()
    return df

@st.cache_data(ttl=60)
def load_stats():
    conn = get_db_connection()
    # Total keseluruhan
    total_all = pd.read_sql_query("SELECT COUNT(*) as count FROM conversations", conn).iloc[0]['count']
    # Total AI handled
    ai_handled = pd.read_sql_query("SELECT COUNT(*) as count FROM conversations WHERE status = 'handled_by_ai'", conn).iloc[0]['count']
    # Hari ini
    today = datetime.now().date().isoformat()
    today_stats = pd.read_sql_query(f"SELECT total_messages, ai_handled, needs_human FROM daily_stats WHERE date = '{today}'", conn)
    conn.close()
    
    return {
        'total_all': total_all,
        'ai_handled': ai_handled,
        'today_total': today_stats.iloc[0]['total_messages'] if not today_stats.empty else 0,
        'today_ai': today_stats.iloc[0]['ai_handled'] if not today_stats.empty else 0,
        'today_human': today_stats.iloc[0]['needs_human'] if not today_stats.empty else 0
    }

# Layout: 4 card stats
stats = load_stats()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📬 Total Pesan", stats['total_all'])
with col2:
    st.metric("🤖 AI Handled", stats['ai_handled'])
with col3:
    st.metric("📅 Hari Ini", stats['today_total'])
with col4:
    st.metric("👤 Perlu Human", stats['today_human'])

st.markdown("---")

# Tab layout
tab1, tab2, tab3 = st.tabs(["📝 Percakapan Terbaru", "📈 Analisis & Grafik", "⚙️ Settings"])

with tab1:
    st.subheader("Percakapan WhatsApp Terbaru")
    df = load_conversations()
    
    if not df.empty:
        # Filter by date
        col_filter, col_search = st.columns([2, 1])
        with col_filter:
            date_filter = st.date_input("Filter tanggal", value=None)
        with col_search:
            search_term = st.text_input("Cari pesan", placeholder="Ketik kata kunci...")
        
        # Apply filters
        if date_filter:
            df = df[pd.to_datetime(df['created_at']).dt.date == date_filter]
        if search_term:
            df = df[df['message'].str.contains(search_term, case=False) | 
                    df['reply'].str.contains(search_term, case=False)]
        
        # Display conversations
        for _, row in df.iterrows():
            with st.expander(f"📱 {row['customer_name']} ({row['customer_phone']}) - {row['created_at']}"):
                st.markdown(f"**Customer:** {row['customer_name']} ({row['customer_company']})")
                st.markdown(f"**📤 Pesan:** {row['message']}")
                st.markdown(f"**🤖 Balasan AI:** {row['reply']}")
                st.markdown(f"**🏷️ Status:** {row['status']}")
    else:
        st.info("Belum ada percakapan. Tunggu chat dari customer!")

with tab2:
    st.subheader("📊 Statistik & Visualisasi")
    
    df = load_conversations()
    
    if not df.empty:
        # Buat kolom date
        df['date'] = pd.to_datetime(df['created_at']).dt.date
        
        # Chart 1: Pesan per hari
        daily_counts = df.groupby('date').size().reset_index(name='count')
        fig1 = px.bar(daily_counts, x='date', y='count', title='Jumlah Pesan per Hari')
        st.plotly_chart(fig1, use_container_width=True)
        
        # Chart 2: AI vs Human (pie)
        status_counts = df['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        fig2 = px.pie(status_counts, values='count', names='status', title='Distribusi Handling')
        st.plotly_chart(fig2, use_container_width=True)
        
        # Chart 3: Top customers
        top_customers = df['customer_name'].value_counts().head(10).reset_index()
        top_customers.columns = ['customer', 'messages']
        fig3 = px.bar(top_customers, x='customer', y='messages', title='Top 10 Customer Paling Aktif')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Belum ada data untuk ditampilkan")

with tab3:
    st.subheader("Pengaturan Dashboard")
    
    # Info database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM conversations")
    total = cursor.fetchone()[0]
    conn.close()
    
    st.write(f"📁 **Database:** `chat_history.db`")
    st.write(f"📊 **Total percakapan tersimpan:** {total}")
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.success("Data berhasil di-refresh!")
        st.rerun()

# Sidebar dengan info
st.sidebar.markdown("---")
st.sidebar.info(
    """
    **💡 Tentang Dashboard Ini**
    - Semua percakapan AI terekam otomatis
    - Update real-time saat chat masuk
    - Bisa filter berdasarkan tanggal
    - Data disimpan di SQLite lokal
    """
)