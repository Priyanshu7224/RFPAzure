#!/usr/bin/env python3
"""
Test script to verify Azure Blob Storage setup
Run this before deploying to production
"""

import os
from dotenv import load_dotenv
from services.azure_storage_service import AzureStorageService

def test_azure_storage():
    """Test Azure Blob Storage connection and operations"""
    print("🧪 Testing Azure Blob Storage Setup")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize storage service
    storage_service = AzureStorageService()
    
    # Check configuration
    storage_info = storage_service.get_storage_info()
    print(f"📊 Storage Type: {storage_info['storage_type']}")
    print(f"🔧 Configured: {storage_info['configured']}")
    print(f"📁 Container: {storage_info['container_name']}")
    
    if not storage_info['configured']:
        print("\n❌ Azure Blob Storage not configured!")
        print("💡 To configure:")
        print("1. Create Azure Storage Account")
        print("2. Add AZURE_STORAGE_CONNECTION_STRING to .env file")
        print("3. Run this test again")
        return False
    
    try:
        # Test file operations
        print("\n🧪 Testing file operations...")
        
        # Test upload
        test_content = b"Test file content for RFP BOM Generator"
        session_id = "test-session-123"
        
        blob_name = storage_service.upload_file(
            test_content, 
            "test-file.txt", 
            session_id, 
            "test"
        )
        print(f"✅ Upload successful: {blob_name}")
        
        # Test download
        downloaded_content = storage_service.download_file(blob_name)
        if downloaded_content == test_content:
            print("✅ Download successful: Content matches")
        else:
            print("❌ Download failed: Content mismatch")
            return False
        
        # Test JSON operations
        test_data = {
            "test": True,
            "message": "Azure Blob Storage is working!",
            "records": 12345
        }
        
        json_blob = storage_service.save_json_data(test_data, session_id, "test_data")
        print(f"✅ JSON save successful: {json_blob}")
        
        loaded_data = storage_service.load_json_data(json_blob)
        if loaded_data == test_data:
            print("✅ JSON load successful: Data matches")
        else:
            print("❌ JSON load failed: Data mismatch")
            return False
        
        # Test file listing
        files = storage_service.list_user_files(session_id)
        print(f"✅ File listing successful: {len(files)} files found")
        
        # Cleanup test files
        storage_service.delete_file(blob_name)
        storage_service.delete_file(json_blob)
        print("✅ Cleanup successful")
        
        print("\n🎉 All tests passed! Azure Blob Storage is ready for production.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("💡 Check your Azure Storage configuration")
        return False

if __name__ == "__main__":
    success = test_azure_storage()
    if success:
        print("\n🚀 Ready to deploy to Azure App Services!")
    else:
        print("\n⚠️  Fix configuration before deploying to production.")
