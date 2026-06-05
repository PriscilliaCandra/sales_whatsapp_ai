import hashlib
import sqlite3
from datetime import datetime
import json
import csv
import os

DB_PATH = "chat_history.db"

def init_db():
    """Buat tabel-tabel yang diperlukan"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabel conversations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_phone TEXT,
            customer_company TEXT,
            message TEXT,
            reply TEXT,
            direction TEXT,
            status TEXT,
            assigned_to TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabel daily_stats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            date DATE PRIMARY KEY,
            total_messages INTEGER DEFAULT 0,
            ai_handled INTEGER DEFAULT 0,
            needs_human INTEGER DEFAULT 0,
            admin_sent INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0
        )
    ''')
    
    # Tabel users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            phone TEXT,
            password_hash TEXT,
            role TEXT CHECK(role IN ('supervisor', 'agent')),
            is_active INTEGER DEFAULT 1,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # Tabel campaigns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            template_name TEXT,
            category TEXT,
            status TEXT DEFAULT 'draft',
            recipient_list TEXT,
            total_recipients INTEGER DEFAULT 0,
            sent_count INTEGER DEFAULT 0,
            delivered_count INTEGER DEFAULT 0,
            created_by INTEGER,
            scheduled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # Tabel templates
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            type TEXT,
            category TEXT,
            language TEXT DEFAULT 'id',
            content TEXT,
            header TEXT,
            footer TEXT,
            status TEXT DEFAULT 'draft',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # Tabel recipient_lists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipient_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            channel TEXT DEFAULT 'WhatsApp',
            contacts_count INTEGER DEFAULT 0,
            upload_status TEXT DEFAULT 'pending',
            source TEXT,
            file_path TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # Tabel chat_assignments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            customer_phone TEXT,
            assigned_to INTEGER,
            assigned_by INTEGER,
            status TEXT DEFAULT 'open',
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (assigned_to) REFERENCES users(id),
            FOREIGN KEY (assigned_by) REFERENCES users(id),
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    ''')
    
    # Insert default admin user (password: admin123)
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, phone, password_hash, role, created_by)
        VALUES ('admin', 'admin@indotrading.com', '628118131010', ?, 'supervisor', NULL)
    ''', (hashlib.sha256('admin123'.encode()).hexdigest(),))
    
    conn.commit()
    conn.close()
    print("✅ Database siap!")

# ============ FUNGSI UNTUK CONVERSATIONS ============
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
    update_daily_stats()

def save_admin_message(customer_phone, message):
    """Simpan pesan yang dikirim admin ke database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    customer_name = "Customer"
    customer_company = ""
    
    try:
        cursor.execute("SELECT customer_name, customer_company FROM conversations WHERE customer_phone = ? ORDER BY created_at DESC LIMIT 1", (customer_phone,))
        row = cursor.fetchone()
        if row:
            customer_name = row[0] or "Customer"
            customer_company = row[1] or ""
    except:
        pass
    
    cursor.execute('''
        INSERT INTO conversations 
        (customer_name, customer_phone, customer_company, message, reply, direction, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (customer_name, customer_phone, customer_company, 
          message, "", "outgoing", "admin_sent", datetime.now()))
    
    conn.commit()
    conn.close()
    update_daily_stats()

def update_daily_stats():
    """Update statistik harian"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = datetime.now().date().isoformat()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'handled_by_ai' THEN 1 ELSE 0 END) as ai_handled,
            SUM(CASE WHEN status = 'needs_human' THEN 1 ELSE 0 END) as needs_human,
            SUM(CASE WHEN status = 'admin_sent' THEN 1 ELSE 0 END) as admin_sent
        FROM conversations 
        WHERE DATE(created_at) = ?
    ''', (today,))
    
    row = cursor.fetchone()
    total, ai_handled, needs_human, admin_sent = row[0] or 0, row[1] or 0, row[2] or 0, row[3] or 0
    
    cursor.execute('''
        INSERT OR REPLACE INTO daily_stats (date, total_messages, ai_handled, needs_human, admin_sent)
        VALUES (?, ?, ?, ?, ?)
    ''', (today, total, ai_handled, needs_human, admin_sent))
    
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
    
    cursor.execute('SELECT COUNT(*) FROM conversations')
    total_all = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM conversations WHERE status = "handled_by_ai"')
    ai_handled = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM conversations WHERE status = "admin_sent"')
    admin_sent = cursor.fetchone()[0] or 0
    
    today = datetime.now().date().isoformat()
    cursor.execute('SELECT total_messages, ai_handled, needs_human, admin_sent FROM daily_stats WHERE date = ?', (today,))
    row = cursor.fetchone()
    
    conn.close()
    
    return {
        'total_all': total_all,
        'ai_handled': ai_handled,
        'admin_sent': admin_sent,
        'today_total': row[0] if row else 0,
        'today_ai': row[1] if row else 0,
        'today_human': row[2] if row else 0,
        'today_admin': row[3] if row else 0
    }

# ============ FUNGSI UNTUK USERS ============
def get_users(role=None):
    """Ambil daftar users"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if role:
        cursor.execute("SELECT * FROM users WHERE role = ? AND is_active = 1", (role,))
    else:
        cursor.execute("SELECT * FROM users WHERE is_active = 1")
    
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

def get_user_by_id(user_id):
    """Ambil user berdasarkan ID"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    user = dict(row) if row else None
    conn.close()
    return user

# ============ FUNGSI UNTUK CAMPAIGNS ============
def create_campaign(data):
    """Buat campaign baru"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO campaigns (name, template_name, category, recipient_list, total_recipients, created_by, scheduled_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['name'], data['template_name'], data['category'], 
          data['recipient_list'], data['total_recipients'], 
          data['created_by'], data.get('scheduled_at')))
    
    campaign_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return campaign_id

def get_campaigns():
    """Ambil semua campaigns"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.*, u.username as creator 
        FROM campaigns c
        LEFT JOIN users u ON c.created_by = u.id
        ORDER BY c.created_at DESC
    ''')
    
    campaigns = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return campaigns

def update_campaign_status(campaign_id, status, sent_count=None):
    """Update status campaign"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if sent_count is not None:
        cursor.execute('''
            UPDATE campaigns SET status = ?, sent_count = ? WHERE id = ?
        ''', (status, sent_count, campaign_id))
    else:
        cursor.execute('''
            UPDATE campaigns SET status = ? WHERE id = ?
        ''', (status, campaign_id))
    
    conn.commit()
    conn.close()

# ============ FUNGSI UNTUK BROADCAST ============
def get_recipient_numbers(recipient_list_name):
    """Ambil daftar nomor dari recipient list"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT file_path FROM recipient_lists WHERE name = ?", (recipient_list_name,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not row[0]:
        print(f"File path not found for: {recipient_list_name}")
        return []
    
    file_path = row[0]
    numbers = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Baca baris pertama untuk deteksi delimiter
            first_line = f.readline().strip()
            f.seek(0)
            
            # Deteksi delimiter (koma atau titik koma)
            if ',' in first_line:
                delimiter = ','
            elif ';' in first_line:
                delimiter = ';'
            else:
                delimiter = ','
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row in reader:
                # Cari kolom nomor (case insensitive)
                nomor = None
                for key in row.keys():
                    key_lower = key.lower().strip()
                    if key_lower in ['nomor', 'phone', 'no', 'number', 'whatsapp', 'hp', 'telepon']:
                        nomor = row[key]
                        break
                
                # Jika tidak ditemukan, ambil kolom pertama
                if not nomor and len(row) > 0:
                    nomor = list(row.values())[0]
                
                if nomor:
                    # Bersihkan nomor
                    nomor = str(nomor).strip().replace(' ', '').replace('+', '').replace('-', '')
                    if nomor.startswith('0'):
                        nomor = '62' + nomor[1:]
                    elif not nomor.startswith('62') and nomor.isdigit():
                        nomor = '62' + nomor
                    
                    if nomor and len(nomor) >= 10:
                        numbers.append(nomor)
                        print(f"Found number: {nomor}")
            
            print(f"Total numbers found: {len(numbers)}")
            
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    
    return numbers

def send_broadcast_campaign(campaign_id):
    """Kirim campaign broadcast ke semua recipient"""
    from config import ACCESS_TOKEN, PHONE_NUMBER_ID
    import requests
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ambil data campaign
    cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    campaign = cursor.fetchone()
    
    if not campaign:
        conn.close()
        return False, "Campaign tidak ditemukan"
    
    # Ambil data campaign
    campaign_name = campaign[1]
    template_name = campaign[2]
    recipient_list_name = campaign[5]
    
    # Ambil daftar nomor dari recipient list
    recipients = get_recipient_numbers(recipient_list_name)
    
    if not recipients:
        conn.close()
        return False, f"Tidak ada nomor di recipient list '{recipient_list_name}'"
    
    # Update total recipients
    cursor.execute("UPDATE campaigns SET total_recipients = ? WHERE id = ?", (len(recipients), campaign_id))
    conn.commit()
    
    # Kirim ke setiap nomor
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    success_count = 0
    failed_numbers = []
    
    for recipient in recipients:
        # Payload untuk template WA
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en"}
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                success_count += 1
                print(f"✅ Terkirim ke {recipient}")
            else:
                failed_numbers.append(recipient)
                print(f"❌ Gagal ke {recipient}: {response.text}")
        except Exception as e:
            failed_numbers.append(recipient)
            print(f"❌ Error ke {recipient}: {e}")
    
    # Update campaign status
    status = 'completed' if success_count > 0 else 'failed'
    cursor.execute('''
        UPDATE campaigns SET status = ?, sent_count = ? WHERE id = ?
    ''', (status, success_count, campaign_id))
    conn.commit()
    conn.close()
    
    if success_count == len(recipients):
        return True, f"✅ Berhasil mengirim ke semua {success_count} nomor!"
    elif success_count > 0:
        return True, f"⚠️ Berhasil {success_count}/{len(recipients)} nomor. Gagal: {len(failed_numbers)} nomor."
    else:
        return False, f"❌ Gagal mengirim ke semua {len(recipients)} nomor. Pastikan template sudah APPROVED."

def send_test_broadcast(template_name, phone_number):
    """Kirim test broadcast ke satu nomor"""
    from config import ACCESS_TOKEN, PHONE_NUMBER_ID
    import requests
    
    # Format nomor
    phone_number = str(phone_number).strip().replace(' ', '').replace('+', '')
    if phone_number.startswith('0'):
        phone_number = '62' + phone_number[1:]
    elif not phone_number.startswith('62'):
        phone_number = '62' + phone_number
    
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "id"}
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return True, f"✅ Test berhasil! Pesan terkirim ke {phone_number}"
        else:
            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
            return False, f"❌ Gagal: {error_msg}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

# ============ FUNGSI UNTUK TEMPLATES ============
def create_template(data):
    """Buat template baru"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO templates (name, type, category, language, content, header, footer, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['name'], data['type'], data['category'], data['language'],
          data['content'], data.get('header'), data.get('footer'), data['created_by']))
    
    template_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return template_id

def get_templates():
    """Ambil semua templates"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.*, u.username as creator 
        FROM templates t
        LEFT JOIN users u ON t.created_by = u.id
        ORDER BY t.created_at DESC
    ''')
    
    templates = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return templates

# ============ FUNGSI UNTUK RECIPIENT LISTS ============
def create_recipient_list(data):
    """Buat recipient list"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO recipient_lists (name, channel, contacts_count, upload_status, source, file_path, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['name'], data['channel'], data['contacts_count'], 
          data['upload_status'], data['source'], data.get('file_path'), data['created_by']))
    
    list_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return list_id

def get_recipient_lists():
    """Ambil semua recipient lists"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.*, u.username as creator 
        FROM recipient_lists r
        LEFT JOIN users u ON r.created_by = u.id
        ORDER BY r.created_at DESC
    ''')
    
    lists = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return lists

def delete_recipient_list(list_id):
    """Hapus recipient list berdasarkan ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ambil file_path dulu
    cursor.execute("SELECT file_path FROM recipient_lists WHERE id = ?", (list_id,))
    row = cursor.fetchone()
    if row and row[0]:
        try:
            os.remove(row[0])
        except:
            pass
    
    cursor.execute("DELETE FROM recipient_lists WHERE id = ?", (list_id,))
    conn.commit()
    conn.close()

# ============ FUNGSI UNTUK CHAT ASSIGNMENTS ============
def assign_chat(conversation_id, customer_phone, assigned_to, assigned_by):
    """Assign chat ke agent"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO chat_assignments (conversation_id, customer_phone, assigned_to, assigned_by)
        VALUES (?, ?, ?, ?)
    ''', (conversation_id, customer_phone, assigned_to, assigned_by))
    
    cursor.execute('''
        UPDATE conversations SET assigned_to = ? WHERE id = ?
    ''', (assigned_to, conversation_id))
    
    conn.commit()
    conn.close()

def get_assigned_chats(agent_id, status='open'):
    """Ambil chat yang diassign ke agent"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM chat_assignments 
        WHERE assigned_to = ? AND status = ?
        ORDER BY assigned_at DESC
    ''', (agent_id, status))
    
    assignments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return assignments

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized!")