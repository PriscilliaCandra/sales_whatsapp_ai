# bulk_sender.py
import requests
import time
from datetime import datetime
from config import PHONE_NUMBER_ID, ACCESS_TOKEN, TEMPLATE_NAME
from spreadsheet_handler import SpreadsheetHandler

class BulkSender:
    """Kirim WA massal ke customer dari spreadsheet"""
    
    def __init__(self):
        self.api_url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        self.spreadsheet = SpreadsheetHandler()
    
    def format_phone_number(self, nomor):
        """Format nomor ke format internasional 628xxx"""
        nomor = str(nomor).strip().replace("+", "").replace(" ", "").replace("-", "")
        
        if nomor.startswith("0"):
            nomor = "62" + nomor[1:]
        elif not nomor.startswith("62"):
            nomor = "62" + nomor
        
        return nomor
    
    def send_template_message(self, phone_number, nama, perusahaan):
        """Kirim template WA"""
        
        phone_number = self.format_phone_number(phone_number)
        
        # Template tanpa parameter (sesuai template test_ai)
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "template",
            "template": {
                "name": TEMPLATE_NAME,
                "language": {"code": "en"}
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            if response.status_code == 200:
                print(f"   ✅ BERHASIL -> {nama} ({phone_number})")
                return "Sent", timestamp
            else:
                print(f"   ❌ GAGAL -> {nama}: {response.status_code}")
                print(f"      Error: {response.text}")
                return "Failed", timestamp
        except Exception as e:
            print(f"   ❌ ERROR -> {nama}: {e}")
            return "Failed", datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    def send_all_pending(self, delay=2):
        """Kirim ke semua customer yang pending"""
        
        print("="*60)
        print("📱 MEMULAI BULK WA SENDER")
        print("="*60)
        
        # Tambah kolom tracking jika perlu
        self.spreadsheet.add_tracking_columns()
        
        # Ambil customer yang pending
        pending = self.spreadsheet.get_pending_customers()
        
        if not pending:
            print("✅ Tidak ada customer yang perlu dikirim!")
            return
        
        print(f"📊 Menemukan {len(pending)} customer untuk dikirim")
        print("="*60)
        
        sent_count = 0
        failed_count = 0
        
        for i, customer in enumerate(pending, 1):
            print(f"\n📤 [{i}/{len(pending)}] Mengirim ke {customer['nama']}")
            print(f"   📞 Nomor: {customer['nomor']}")
            print(f"   🏢 Perusahaan: {customer['perusahaan']}")
            
            status, timestamp = self.send_template_message(
                customer['nomor'],
                customer['nama'],
                customer['perusahaan']
            )
            
            # Update spreadsheet
            self.spreadsheet.update_status(customer['row_index'], status, timestamp)
            
            if status == "Sent":
                sent_count += 1
            else:
                failed_count += 1
            
            if i < len(pending):
                print(f"   ⏳ Tunggu {delay} detik...")
                time.sleep(delay)
        
        print("\n" + "="*60)
        print("📊 RINGKASAN BULK SENDER")
        print("="*60)
        print(f"✅ Berhasil: {sent_count}")
        print(f"❌ Gagal: {failed_count}")
        print(f"📝 Total: {sent_count + failed_count}")
        print("="*60)


if __name__ == "__main__":
    sender = BulkSender()
    sender.send_all_pending(delay=2)