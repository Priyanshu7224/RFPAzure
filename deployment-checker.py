#!/usr/bin/env python3
"""
Deployment Readiness Checker for Azure App Services
"""

import os
import sys
from dotenv import load_dotenv

def check_deployment_readiness():
    """Check if app is ready for Azure App Services deployment"""
    print("🚀 Azure App Services Deployment Readiness Check")
    print("=" * 60)
    
    load_dotenv()
    
    issues = []
    warnings = []
    
    # Check Azure OpenAI configuration
    print("\n🤖 Azure OpenAI Configuration:")
    openai_key = os.getenv('AZURE_OPENAI_API_KEY')
    openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    openai_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
    
    if openai_key and openai_endpoint and openai_deployment:
        print("✅ Azure OpenAI configured")
    else:
        issues.append("❌ Azure OpenAI not fully configured")
        print("❌ Missing Azure OpenAI configuration")
    
    # Check storage configuration
    print("\n💾 Storage Configuration:")
    storage_conn = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    
    if storage_conn:
        print("✅ Azure Blob Storage configured")
        print("✅ Ready for production with persistent storage")
    else:
        warnings.append("⚠️  Azure Blob Storage not configured")
        print("⚠️  Using local storage (will not work properly in production)")
        print("💡 Recommendation: Set up Azure Blob Storage")
    
    # Check secret key
    print("\n🔐 Security Configuration:")
    secret_key = os.getenv('SECRET_KEY')
    
    if secret_key and secret_key != 'dev-secret-key-change-in-production':
        print("✅ Production secret key configured")
    else:
        issues.append("❌ Using development secret key")
        print("❌ Change SECRET_KEY for production")
    
    # Check file structure
    print("\n📁 File Structure:")
    required_files = [
        'app.py',
        'requirements.txt',
        'services/azure_openai_service.py',
        'services/stock_master_service.py',
        'services/azure_storage_service.py',
        'templates/index.html'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            missing_files.append(file)
            print(f"❌ {file}")
    
    if missing_files:
        issues.append(f"❌ Missing files: {', '.join(missing_files)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    if not issues:
        if not warnings:
            print("🎉 READY FOR PRODUCTION DEPLOYMENT!")
            print("✅ All checks passed")
            print("🚀 You can deploy to Azure App Services now")
        else:
            print("⚠️  READY WITH LIMITATIONS")
            print("✅ Can deploy but with reduced functionality")
            for warning in warnings:
                print(f"   {warning}")
    else:
        print("❌ NOT READY FOR DEPLOYMENT")
        print("🔧 Fix these issues first:")
        for issue in issues:
            print(f"   {issue}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if not storage_conn:
        print("1. Set up Azure Blob Storage for production:")
        print("   - Create Azure Storage Account")
        print("   - Add AZURE_STORAGE_CONNECTION_STRING to app settings")
        print("   - This enables full functionality with large files")
    
    if secret_key == 'dev-secret-key-change-in-production':
        print("2. Generate production secret key:")
        print("   - Use: python -c 'import secrets; print(secrets.token_hex(32))'")
        print("   - Add to Azure App Service configuration")
    
    print("3. Test deployment:")
    print("   - Deploy to staging slot first")
    print("   - Test file upload/processing")
    print("   - Verify session management")
    
    return len(issues) == 0

if __name__ == "__main__":
    ready = check_deployment_readiness()
    sys.exit(0 if ready else 1)
