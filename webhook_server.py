# webhook_server.py
from flask import Flask, request, jsonify
import requests
from datetime import datetime
import json
import re

from config import PHONE_NUMBER_ID, ACCESS_TOKEN, VERIFY_TOKEN
from spreadsheet_handler import SpreadsheetHandler
from ai_handler import AIHandler
from database import init_db, save_conversation, get_stats, get_all_conversations

app = Flask(__name__)

init_db()

# Inisialisasi handler
spreadsheet = SpreadsheetHandler()
ai = AIHandler()

# URL API WhatsApp
WHATSAPP_API_URL = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

def format_phone_number(nomor):
    """Format nomor ke internasional"""
    nomor = str(nomor).strip().replace("+", "").replace(" ", "").replace("-", "")
    if nomor.startswith("0"):
        nomor = "62" + nomor[1:]
    elif not nomor.startswith("62"):
        nomor = "62" + nomor
    return nomor

def send_whatsapp_message(to_number, message):
    """Kirim pesan WA bebas (bukan template)"""
    
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
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"   ✅ Balasan terkirim ke {to_number}")
            return True
        else:
            print(f"   ❌ Gagal kirim: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Verifikasi webhook (wajib Meta)"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode and token and mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook terverifikasi!")
        return challenge, 200
    return "Verifikasi gagal", 403

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """Terima dan balas pesan WA masuk"""
    
    data = request.json
    
    try:
        # Ambil pesan dari webhook
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return "OK", 200
        
        message = messages[0]
        from_number = message.get("from")
        msg_type = message.get("type")
        
        # Hanya proses pesan teks
        if msg_type != "text":
            # Balas dengan pesan hanya menerima teks
            send_whatsapp_message(from_number, "Maaf, saya hanya bisa membaca pesan teks.")
            return "OK", 200
        
        user_message = message.get("text", {}).get("body", "")
        print(f"\n📩 Dari {from_number}: {user_message}")
        
        # Cari data customer di spreadsheet
        customer = spreadsheet.get_customer_by_phone(from_number)
        
        if customer:
            customer_name = customer['nama']
            customer_company = customer['perusahaan']
            print(f"   👤 Customer: {customer_name} - {customer_company}")
        else:
            customer_name = "Customer"
            customer_company = ""
            print(f"   👤 Customer baru (belum ada di database)")
        
        # Cek apakah Ollama berjalan
        # if not ai.is_ollama_running():
        #     print("   ⚠️ Ollama tidak berjalan! Kirim balasan default.")
        #     fallback_reply = "Terima kasih pesannya. Tim sales kami akan segera menghubungi Anda. (Layanan AI sedang maintenance)"
        #     send_whatsapp_message(from_number, fallback_reply)
        #     return "OK", 200
        
        # Dapatkan balasan dari AI
        print("   🤔 AI sedang memproses...")
        ai_reply = ai.get_response(user_message, customer_name, customer_company)
        print(f"   🤖 AI balas: {ai_reply}")
        
        # Kirim balasan
        send_whatsapp_message(from_number, ai_reply)
        
        # Simpan chat history ke spreadsheet (opsional)
        # Bisa ditambahkan nanti
        
        # Simpan ke database untuk dashboard
        save_conversation(
            customer_name=customer_name,
            customer_phone=from_number,
            customer_company=customer_company,
            message=user_message,
            reply=ai_reply,
            direction="incoming",
            status="handled_by_ai"
        )
        
    except Exception as e:
        print(f"❌ Error webhook: {e}")
        
         # Simpan error ke database
        try:
            save_conversation(
                customer_name="Unknown",
                customer_phone=from_number if 'from_number' in locals() else "Unknown",
                customer_company="Unknown",
                message=user_message if 'user_message' in locals() else "Unknown",
                reply=f"Error: {str(e)}",
                direction="incoming",
                status="error"
            )
        except:
            pass
    
    return "OK", 200

# ============ API ENDPOINTS UNTUK DASHBOARD ============

@app.route("/api/conversations", methods=["GET"])
def api_get_conversations():
    """API untuk mengambil semua percakapan (dipakai dashboard)"""
    limit = request.args.get("limit", 100, type=int)
    conversations = get_all_conversations(limit)
    return jsonify({
        "success": True,
        "data": conversations,
        "total": len(conversations)
    })

@app.route("/api/stats", methods=["GET"])
def api_get_stats():
    """API untuk mengambil statistik (dipakai dashboard)"""
    stats = get_stats()
    return jsonify({
        "success": True,
        "data": stats
    })
    
@app.route("/api/conversations/phone/<phone>", methods=["GET"])
def api_get_conversations_by_phone(phone):
    """API untuk mengambil percakapan berdasarkan nomor telepon"""
    conversations = get_all_conversations(limit=500)
    filtered = [c for c in conversations if c.get('customer_phone') == phone]
    return jsonify({
        "success": True,
        "data": filtered,
        "total": len(filtered)
    })

@app.route("/health", methods=["GET"])
def health_check():
    """Cek status server"""
    ollama_status = "running" if ai.is_ollama_running() else "stopped"
    return jsonify({
        "status": "ok",
        "ollama": ollama_status,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    print("="*60)
    print("🤖 WHATSAPP AI WEBHOOK SERVER")
    print("="*60)
    print(f"📡 Webhook URL: http://localhost:5000/webhook")
    print(f"🔐 Verify Token: {VERIFY_TOKEN}")
    print(f"🔍 Health check: http://localhost:5000/health")
    print("="*60)
    
    # Cek Ollama
    if ai.is_ollama_running():
        print("✅ Ollama berjalan (AI siap)")
    else:
        print("❌ Ollama TIDAK berjalan!")
        print("   Jalankan 'ollama serve' di terminal terpisah")
        print("   Download model: ollama pull llama3.2:3b")
    print("="*60)
    
    app.run(port=5000, debug=True)