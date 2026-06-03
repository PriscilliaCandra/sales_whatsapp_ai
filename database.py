# database.py
import sqlite3
from datetime import datetime
import json

DB_PATH = "chat_history.db"

def init_db():
    """Buat tabel-tabel yang diperlukan"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabel untuk menyimpan semua percakapan
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_phone TEXT,
            customer_company TEXT,
            message TEXT,
            reply TEXT,
            direction TEXT,  -- 'incoming' atau 'outgoing'
            status TEXT,     -- 'handled_by_ai', 'needs_human', 'escalated'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabel untuk ringkasan performa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            date DATE PRIMARY KEY,
            total_messages INTEGER DEFAULT 0,
            ai_handled INTEGER DEFAULT 0,
            needs_human INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database siap!")

def save_conversation(customer_name, customer_phone, customer_company, 
                      message, reply, direction, status="handled_by_ai"):
    """Simpan percakapan ke database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO conversations 
        (customer_name, customer_phone, customer_company, message, reply, direction, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (customer_name, customer_phone, customer_company, 
          message, reply, direction, status, datetime.now()))
    
    conn.commit()
    conn.close()
    
    # Update daily stats
    update_daily_stats()

def update_daily_stats():
    """Update statistik harian"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = datetime.now().date().isoformat()
    
    # Hitung total hari ini
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'handled_by_ai' THEN 1 ELSE 0 END) as ai_handled,
            SUM(CASE WHEN status = 'needs_human' THEN 1 ELSE 0 END) as needs_human
        FROM conversations 
        WHERE DATE(created_at) = ?
    ''', (today,))
    
    row = cursor.fetchone()
    total, ai_handled, needs_human = row[0] or 0, row[1] or 0, row[2] or 0
    
    # Insert atau replace
    cursor.execute('''
        INSERT OR REPLACE INTO daily_stats (date, total_messages, ai_handled, needs_human)
        VALUES (?, ?, ?, ?)
    ''', (today, total, ai_handled, needs_human))
    
    conn.commit()
    conn.close()

def get_all_conversations(limit=100):
    """Ambil semua percakapan"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM conversations 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (limit,))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def get_stats():
    """Ambil statistik untuk dashboard"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total keseluruhan
    cursor.execute('SELECT COUNT(*) FROM conversations')
    total_all = cursor.fetchone()[0] or 0
    
    # Total AI handled
    cursor.execute('SELECT COUNT(*) FROM conversations WHERE status = "handled_by_ai"')
    ai_handled = cursor.fetchone()[0] or 0
    
    # Hari ini
    today = datetime.now().date().isoformat()
    cursor.execute('SELECT total_messages, ai_handled, needs_human FROM daily_stats WHERE date = ?', (today,))
    row = cursor.fetchone()
    
    conn.close()
    
    return {
        'total_all': total_all,
        'ai_handled': ai_handled,
        'today_total': row[0] if row else 0,
        'today_ai': row[1] if row else 0,
        'today_human': row[2] if row else 0
    }

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized!")