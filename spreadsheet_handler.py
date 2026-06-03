# spreadsheet_handler.py
import gspread
from google.oauth2.service_account import Credentials
from config import SPREADSHEET_NAME, WORKSHEET_NAME

class SpreadsheetHandler:
    """Handler untuk Google Sheets"""
    
    def __init__(self):
        """Konek ke Google Sheets"""
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
        print(f"✅ Berhasil konek ke: {SPREADSHEET_NAME} -> {WORKSHEET_NAME}")
    
    def get_all_customers(self):
        """Ambil semua data customer"""
        data = self.sheet.get_all_values()
        if len(data) <= 1:
            return []
        
        headers = data[0]
        customers = []
        
        for row in data[1:]:
            if len(row) < 3:
                continue
            customers.append({
                'row_index': len(customers) + 2,  # Baris ke berapa di sheet
                'nama': row[1] if len(row) > 1 else "",
                'nomor': row[2] if len(row) > 2 else "",
                'perusahaan': row[3] if len(row) > 3 else "",
                'kebutuhan': row[4] if len(row) > 4 else "",
                'score': row[5] if len(row) > 5 else "",
                'status': row[6] if len(row) > 6 else "",
                'timestamp_kirim': row[7] if len(row) > 7 else ""
            })
        
        return customers
    
    def get_customer_by_phone(self, phone_number):
        """Cari customer berdasarkan nomor WA"""
        customers = self.get_all_customers()
        for customer in customers:
            if customer['nomor'] == phone_number:
                return customer
        return None
    
    def get_pending_customers(self):
        """Ambil customer yang belum dikirim WA"""
        customers = self.get_all_customers()
        pending = [c for c in customers if not c['status'] or c['status'] == '']
        return pending
    
    def update_status(self, row_index, status, timestamp):
        """Update status WA dan timestamp di spreadsheet"""
        from config import COL_STATUS_WA, COL_TIMESTAMP_KIRIM
        
        # Update kolom G (Status) dan H (Timestamp)
        self.sheet.update(range_name=f"{chr(65+COL_STATUS_WA)}{row_index}", values=[[status]])
        self.sheet.update(range_name=f"{chr(65+COL_TIMESTAMP_KIRIM)}{row_index}", values=[[timestamp]])
        print(f"📝 Update baris {row_index}: {status}")
    
    def add_tracking_columns(self):
        """Tambahkan kolom Status & Timestamp jika belum ada"""
        headers = self.sheet.row_values(1)
        
        from config import COL_STATUS_WA, COL_TIMESTAMP_KIRIM
        
        if len(headers) <= COL_STATUS_WA:
            self.sheet.update_cell(1, COL_STATUS_WA + 1, "Status WA")
            print("✅ Menambahkan kolom 'Status WA'")
        
        if len(headers) <= COL_TIMESTAMP_KIRIM:
            self.sheet.update_cell(1, COL_TIMESTAMP_KIRIM + 1, "Timestamp Kirim")
            print("✅ Menambahkan kolom 'Timestamp Kirim'")
    
    def get_cell_value(self, row, col):
        """Amil nilai dari cell tertentu"""
        try:
            return self.sheet.cell(row, col).value
        except:
            return ""
    
    def update_cell(self, row, col, value):
        """Update nilai cell tertentu"""
        self.sheet.update_cell(row, col, value)