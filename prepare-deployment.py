#!/usr/bin/env python3
"""
Prepare deployment package for Azure App Services
"""

import os
import shutil
import zipfile
from pathlib import Path

def prepare_deployment():
    """Create deployment package"""
    print("📦 Preparing Azure App Services Deployment Package")
    print("=" * 60)
    
    # Create deployment directory
    deploy_dir = "azure-deployment"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    
    # Files and directories to include
    include_items = [
        "app.py",
        "requirements.txt",
        "services/",
        "templates/",
        "static/",
        "utils/"
    ]
    
    # Copy files
    print("\n📁 Copying files...")
    for item in include_items:
        if os.path.exists(item):
            if os.path.isfile(item):
                shutil.copy2(item, deploy_dir)
                print(f"✅ Copied file: {item}")
            else:
                shutil.copytree(item, os.path.join(deploy_dir, item))
                print(f"✅ Copied directory: {item}")
        else:
            print(f"⚠️  Not found: {item}")
    
    # Update requirements.txt to include azure-storage-blob
    req_file = os.path.join(deploy_dir, "requirements.txt")
    if os.path.exists(req_file):
        with open(req_file, 'r') as f:
            requirements = f.read()
        
        if 'azure-storage-blob' not in requirements:
            with open(req_file, 'a') as f:
                f.write('\nazure-storage-blob==12.25.1\n')
            print("✅ Added azure-storage-blob to requirements.txt")
    
    # Create startup command file
    startup_file = os.path.join(deploy_dir, "startup.txt")
    with open(startup_file, 'w') as f:
        f.write("gunicorn --bind=0.0.0.0 --timeout 600 app:app\n")
    print("✅ Created startup.txt")
    
    # Create .deployment file
    deployment_file = os.path.join(deploy_dir, ".deployment")
    with open(deployment_file, 'w') as f:
        f.write("""[config]
command = bash deploy.sh
""")
    
    # Create deploy.sh
    deploy_script = os.path.join(deploy_dir, "deploy.sh")
    with open(deploy_script, 'w') as f:
        f.write("""#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
""")
    
    print("✅ Created deployment configuration")
    
    # Create ZIP file
    zip_filename = "rfp-bom-generator.zip"
    print(f"\n📦 Creating ZIP package: {zip_filename}")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, deploy_dir)
                zipf.write(file_path, arc_name)
                print(f"   Added: {arc_name}")
    
    print(f"\n🎉 Deployment package ready: {zip_filename}")
    print(f"📁 Package contents in: {deploy_dir}/")
    
    # Instructions
    print("\n" + "=" * 60)
    print("📋 DEPLOYMENT INSTRUCTIONS")
    print("=" * 60)
    print("1. Go to your Azure App Service in the portal")
    print("2. Navigate to 'Deployment Center'")
    print("3. Choose 'ZIP Deploy'")
    print(f"4. Upload the file: {zip_filename}")
    print("5. Wait for deployment to complete")
    print("6. Test your application!")
    
    return zip_filename

if __name__ == "__main__":
    prepare_deployment()
