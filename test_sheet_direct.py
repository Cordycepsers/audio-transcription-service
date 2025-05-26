#!/usr/bin/env python3
"""
Direct test of Google Sheets integration
"""
import gspread
import sys
from datetime import datetime

def test_sheet_direct():
    """Test direct access to Google Sheet"""
    try:
        print("\n🔑 Authenticating with service account...")
        gc = gspread.service_account(filename='service-account.json')
        
        print("📝 Opening spreadsheet...")
        sheet = gc.open_by_key("1s6OxhfqfQfxHH4M4ln1C1hrN3DWM8HI_-QJlY_p-KRU")
        print(f"✓ Opened sheet: {sheet.title}")
        
        print("\n📊 Accessing worksheet 'TRANSCRIPT FINAL'...")
        try:
            worksheet = sheet.worksheet("TRANSCRIPT FINAL")
            print("✓ Found worksheet")
            
            # Get current content
            print("\n📋 Current content:")
            values = worksheet.get_all_values()
            if values:
                for row in values[:5]:  # Show first 5 rows
                    print(row)
                if len(values) > 5:
                    print(f"... and {len(values)-5} more rows")
            else:
                print("(Sheet is empty)")
            
            # Add a test row
            print("\n➕ Adding test row...")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_row = [timestamp, "test_direct.mp4", "Direct test transcript"]
            worksheet.append_row(new_row)
            print("✓ Added test row successfully")
            
        except gspread.exceptions.WorksheetNotFound:
            print("❌ Worksheet 'TRANSCRIPT FINAL' not found!")
            print("\n📑 Available worksheets:")
            for ws in sheet.worksheets():
                print(f"  - {ws.title}")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nDebug information:")
        print(f"Python version: {sys.version}")
        print(f"gspread version: {gspread.__version__}")

if __name__ == "__main__":
    test_sheet_direct()
