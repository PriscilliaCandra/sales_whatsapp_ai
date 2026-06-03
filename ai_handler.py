# ai_handler.py
import requests
import json
import time
import re  # ✅ IMPORT RE UNTUK CLEANING

from config import OPENROUTER_API_KEY

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class AIHandler:
    def __init__(self):
        self.model = "openrouter/free"
        self.api_url = OPENROUTER_URL
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        self.conversation_history = {}
        print("✅ AI Handler siap (OpenRouter)")
    
    def is_ollama_running(self):
        try:
            response = requests.get("https://openrouter.ai/api/v1/models", headers=self.headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _clean_reply(self, reply):
        """Hapus tag think dan response dari balasan AI"""
        if not reply:
            return reply
        # Hapus tag <think>...</think> (termasuk isinya)
        cleaned = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL)
        # Hapus tag <response>...</response> jika ada
        cleaned = re.sub(r'<response>.*?</response>', '', cleaned, flags=re.DOTALL)
        # Hapus teks "thinking..." di awal
        cleaned = re.sub(r'^thinking\.\.\.\s*', '', cleaned, flags=re.IGNORECASE)
        # Hapus garis miring dan spasi berlebih
        cleaned = cleaned.strip()
        return cleaned
    
    def _get_openrouter_response(self, prompt, retry_count=0):
        """Fungsi internal dengan retry mechanism"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Kamu adalah asisten sales PT Indotrading.com. Balas singkat (3-4 kalimat) dalam bahasa Indonesia yang ramah. JANGAN gunakan tag think atau XML. Langsung berikan jawaban."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 300
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=45)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and 'choices' in data and len(data['choices']) > 0:
                    choice = data['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        reply = choice['message']['content']
                        if reply and isinstance(reply, str):
                            reply = self._clean_reply(reply)  # ✅ Panggil fungsi cleaning
                            return reply.strip()
                
                print(f"   ⚠️ Response format tidak dikenal: {data}")
                return "Maaf, saya tidak bisa memproses saat ini. Silakan coba lagi."
                
            elif response.status_code == 429:
                print(f"   ⚠️ Rate limit terkena!")
                if retry_count < 2:
                    wait_time = 5
                    print(f"   ⏳ Menunggu {wait_time} detik sebelum retry...")
                    time.sleep(wait_time)
                    return self._get_openrouter_response(prompt, retry_count + 1)
                else:
                    return "Maaf, sistem sedang padat. Silakan coba lagi nanti."
            else:
                print(f"   ❌ OpenRouter Error: {response.status_code}")
                if response.status_code >= 500 and retry_count < 2:
                    wait_time = 3
                    print(f"   ⏳ Server error, menunggu {wait_time} detik...")
                    time.sleep(wait_time)
                    return self._get_openrouter_response(prompt, retry_count + 1)
                return "Maaf, layanan AI sedang sibuk. Tim kami akan segera menghubungi Anda."
                
        except requests.exceptions.Timeout:
            print("   ⏰ Timeout!")
            if retry_count < 2:
                print("   ⏳ Retry...")
                return self._get_openrouter_response(prompt, retry_count + 1)
            return "Maaf, koneksi lambat. Silakan kirim pesan lagi."
        except Exception as e:
            print(f"   ❌ Exception: {type(e).__name__}: {e}")
            return "Maaf, terjadi kesalahan teknis. Tim kami akan segera menghubungi Anda."

    def get_response(self, user_message, customer_name="Customer", customer_company=""):
        prompt = f"""Customer: {customer_name} dari {customer_company}
Pesan: "{user_message}"

Balasan (ramah, singkat, bahasa Indonesia):"""
        return self._get_openrouter_response(prompt)


# Test
if __name__ == "__main__":
    ai = AIHandler()
    
    if ai.is_ollama_running():
        print("✅ OpenRouter siap digunakan!")
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
        print("❌ Gagal konek ke OpenRouter. Cek API Key di config.py")