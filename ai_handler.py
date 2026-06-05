import requests
import json
import time
import re
import os
import glob

from config import OPENROUTER_API_KEY

# ============ KONFIGURASI OLLAMA (LOKAL, GRATIS) ============
OLLAMA_URL = "http://localhost:11434/api/generate"

class AIHandler:
    def __init__(self):
        self.model = "llama3.2:3b"
        self.api_url = OLLAMA_URL
        self.headers = {
            "Content-Type": "application/json"
        }
        self.conversation_history = {}
        print(f"✅ AI Handler siap (Ollama - {self.model})")
    
    def is_ollama_running(self):
        """Cek apakah Ollama berjalan"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _clean_reply(self, reply):
        """Hapus tag think dan response dari balasan AI"""
        if not reply:
            return reply
        cleaned = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL)
        cleaned = re.sub(r'<response>.*?</response>', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'^thinking\.\.\.\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        return cleaned
    
    # ai_handler.py - Perbaiki timeout

    def _get_ollama_response(self, prompt, retry_count=0):
        """Panggil Ollama untuk mendapatkan balasan"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 300
        }
        
        try:
            # PERBESAR TIMEOUT MENJADI 120 DETIK
            response = requests.post(self.api_url, json=payload, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("response", "")
                if reply:
                    reply = self._clean_reply(reply)
                    return reply.strip()
                else:
                    return "Maaf, saya tidak bisa memproses saat ini."
            else:
                print(f"   ❌ Ollama Error: {response.status_code}")
                if retry_count < 2:
                    time.sleep(2)
                    return self._get_ollama_response(prompt, retry_count + 1)
                return "Maaf, layanan AI sedang sibuk. Tim kami akan segera menghubungi Anda."
                
        except requests.exceptions.Timeout:
            print("   ⏰ Timeout! Ollama membutuhkan waktu lebih lama.")
            if retry_count < 2:
                print("   ⏳ Retry dengan timeout lebih panjang...")
                time.sleep(3)
                return self._get_ollama_response(prompt, retry_count + 1)
            return "Maaf, AI sedang memproses. Silakan coba lagi nanti."
        except Exception as e:
            print(f"   ❌ Exception: {type(e).__name__}: {e}")
            return "Maaf, terjadi kesalahan teknis. Tim kami akan segera menghubungi Anda."
    
    def load_knowledge_base(self):
        """Load semua knowledge dari folder knowledge/"""
        knowledge_text = ""
        if os.path.exists("knowledge"):
            files = glob.glob("knowledge/*.txt")
            for file in files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        knowledge_text += f.read() + "\n\n"
                except:
                    pass
        return knowledge_text
    
    def get_response(self, user_message, customer_name="Customer", customer_company=""):
        # Load knowledge base
        knowledge = self.load_knowledge_base()
        
        prompt = f"""Kamu adalah asisten sales dari PT Indotrading.com, platform B2B untuk cari supplier.

{knowledge if knowledge else ''}

Customer: {customer_name} dari {customer_company}
Pesan: "{user_message}"

Balas dengan ramah, singkat (3-4 kalimat), dan dalam bahasa Indonesia. Gunakan informasi dari knowledge base jika relevan.

Balasan:"""
        return self._get_ollama_response(prompt)


# Test AI
if __name__ == "__main__":
    ai = AIHandler()
    
    if ai.is_ollama_running():
        print("✅ Ollama berjalan!")
        test_messages = [
            "Halo, apa kabar?",
            "Saya butuh supplier makanan"
        ]
        for msg in test_messages:
            print(f"\n📤 Test: {msg}")
            reply = ai.get_response(msg, "Test User", "PT Test")
            print(f"🤖 AI: {reply}")
            time.sleep(2)
    else:
        print("❌ Ollama tidak berjalan!")
        print("   Jalankan 'ollama serve' di terminal terpisah")