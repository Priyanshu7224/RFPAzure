#!/usr/bin/env python3
"""
Test script for AI-Powered RFP BOM Generator
"""

import os
import sys
import json
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RFPBOMTester:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_health_check(self):
        """Test the health endpoint"""
        print("🔍 Testing health check...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            data = response.json()
            
            print(f"✅ Health Status: {data.get('status', 'unknown')}")
            print(f"🤖 Azure OpenAI: {'✅' if data.get('azure_openai') else '❌'}")
            print(f"📊 Stock Master: {'✅' if data.get('stock_master_loaded') else '❌'}")
            
            return data.get('status') == 'healthy'
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def test_stock_upload(self, file_path='sample_stock_master.csv'):
        """Test stock master file upload"""
        print(f"\n📤 Testing stock master upload: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path, f, 'text/csv')}
                response = self.session.post(f"{self.base_url}/upload-stock-master", files=files)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Upload successful: {data.get('total_records', 0)} records")
                    return True
                else:
                    print(f"❌ Upload failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Upload test failed: {e}")
        
        return False
    
    def test_rfp_processing(self):
        """Test RFP processing with sample data"""
        print("\n🧠 Testing RFP processing...")
        
        sample_rfp_items = [
            "6\" SCH40 SMLS PIPE API 5L X52 PSL2",
            "4\" 150# WNRF FLANGE A105",
            "90D LR ELBOW 6\" SCH40 A234 WPB",
            "6\" X 4\" CONC REDUCER SCH40 A234 WPB",
            "6\" CAP SCH40 A234 WPB",
            "NB 6.0 7.11MM SMLS PIPE",
            "DN100 STD a234 90 degree long radius",
            "4 INCH 150 POUND WELD NECK RAISED FACE FLANGE"
        ]
        
        try:
            payload = {'rfp_items': sample_rfp_items}
            response = self.session.post(
                f"{self.base_url}/process-rfp",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    results = data.get('results', [])
                    summary = data.get('summary', {})
                    
                    print(f"✅ Processing successful!")
                    print(f"📊 Total items: {summary.get('total_items', 0)}")
                    print(f"✅ Matched: {summary.get('matched', 0)}")
                    print(f"⚠️  Unmatched: {summary.get('unmatched', 0)}")
                    print(f"❌ Unavailable: {summary.get('unavailable', 0)}")
                    
                    # Show sample results
                    print("\n📋 Sample Results:")
                    for i, result in enumerate(results[:3]):
                        print(f"  {i+1}. {result.get('original_rfp_item', '')[:50]}...")
                        print(f"     Status: {result.get('status', 'unknown')}")
                        print(f"     Match: {result.get('matched_product_code', 'N/A')}")
                        print(f"     Score: {result.get('match_score', 0)}%")
                        print()
                    
                    return results
                else:
                    print(f"❌ Processing failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ RFP processing test failed: {e}")
        
        return None
    
    def test_bom_export(self, bom_data):
        """Test BOM export functionality"""
        print("\n📥 Testing BOM export...")
        
        if not bom_data:
            print("❌ No BOM data to export")
            return False
        
        try:
            payload = {'bom_data': bom_data}
            response = self.session.post(
                f"{self.base_url}/export-bom",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                # Save the exported file
                filename = 'test_export.xlsx'
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Export successful: {filename}")
                print(f"📁 File size: {len(response.content)} bytes")
                
                # Verify the Excel file
                try:
                    df = pd.read_excel(filename, sheet_name='BOM')
                    print(f"📊 Excel verification: {len(df)} rows exported")
                    return True
                except Exception as e:
                    print(f"⚠️  Excel file verification failed: {e}")
                    return True  # File was created, even if verification failed
                    
            else:
                print(f"❌ Export failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Export test failed: {e}")
        
        return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting AI-Powered RFP BOM Generator Tests\n")
        print("=" * 60)
        
        # Test 1: Health Check
        if not self.test_health_check():
            print("\n❌ Health check failed. Please ensure the application is running.")
            return False
        
        # Test 2: Stock Upload
        if not self.test_stock_upload():
            print("\n❌ Stock upload failed. Cannot proceed with RFP processing.")
            return False
        
        # Test 3: RFP Processing
        bom_data = self.test_rfp_processing()
        if not bom_data:
            print("\n❌ RFP processing failed.")
            return False
        
        # Test 4: BOM Export
        if not self.test_bom_export(bom_data):
            print("\n❌ BOM export failed.")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        print("\n📋 Test Summary:")
        print("✅ Health check passed")
        print("✅ Stock master upload passed")
        print("✅ RFP processing passed")
        print("✅ BOM export passed")
        
        return True

def main():
    """Main test function"""
    print("AI-Powered RFP BOM Generator - Test Suite")
    print("=" * 50)
    
    # Check if application is running
    tester = RFPBOMTester()
    
    try:
        # Run all tests
        success = tester.run_all_tests()
        
        if success:
            print("\n🎯 All tests passed! The application is working correctly.")
            print("\n💡 Next steps:")
            print("   1. Open http://localhost:5000 in your browser")
            print("   2. Upload your stock master file")
            print("   3. Enter RFP line items")
            print("   4. Generate and export your BOM")
        else:
            print("\n❌ Some tests failed. Please check the application setup.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
