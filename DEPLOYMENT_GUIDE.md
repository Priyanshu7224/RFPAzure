# 🚀 Azure App Services Deployment Guide

## 📋 **Storage Solutions for Production**

### **Current Implementation Issues**
- ❌ Local file storage won't work in Azure App Services
- ❌ Files disappear when app restarts
- ❌ No data persistence between sessions
- ❌ No multi-user support

### **✅ Solutions Implemented**

## 🔧 **Option 1: Azure Blob Storage (Recommended)**

### **Benefits:**
- ✅ **Persistent Storage**: Files survive app restarts
- ✅ **Scalable**: Handles multiple users and large files
- ✅ **Session-Based**: Each user gets isolated data
- ✅ **Cost-Effective**: Pay only for storage used
- ✅ **Secure**: Built-in encryption and access controls

### **Setup Steps:**

#### **1. Create Azure Storage Account**
```bash
# Using Azure CLI
az storage account create \
    --name rfpbomstorage \
    --resource-group your-resource-group \
    --location eastus \
    --sku Standard_LRS
```

#### **2. Get Connection String**
```bash
az storage account show-connection-string \
    --name rfpbomstorage \
    --resource-group your-resource-group
```

#### **3. Configure Environment Variables**
Add to your Azure App Service Configuration:

```env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=rfpbomstorage;AccountKey=...
AZURE_CONTAINER_NAME=rfp-bom-data
SECRET_KEY=your-production-secret-key-here
```

## 🔧 **Option 2: Azure Database (Alternative)**

### **For Structured Data Storage:**
- **Azure SQL Database**: For relational data
- **Azure Cosmos DB**: For NoSQL document storage
- **Azure Database for PostgreSQL**: Open-source option

## 📁 **How User Data is Now Managed**

### **Session-Based Isolation**
```
User Session ID: abc-123-def-456
├── Stock Master Files
│   ├── abc-123-def-456/stock/20250108_143022_stock_master.csv
│   └── abc-123-def-456/data/stock_master.json
├── RFP Files
│   ├── abc-123-def-456/rfp/20250108_143045_rfp_items.xlsx
│   └── abc-123-def-456/rfp/20250108_143102_rfp_items.pdf
└── Export Files
    └── abc-123-def-456/export/20250108_143200_generated_bom.xlsx
```

### **User Experience**
1. **First Visit**: User gets unique session ID
2. **Upload Stock Master**: Stored in user's session folder
3. **Process RFP**: Uses user's specific stock data
4. **Export BOM**: Saved to user's export folder
5. **Session Persistence**: Data available for 24 hours

## 🚀 **Deployment Steps**

### **1. Prepare for Deployment**
```bash
# Install production dependencies
pip install azure-storage-blob==12.19.0

# Update requirements.txt
echo "azure-storage-blob==12.19.0" >> requirements.txt
```

### **2. Deploy to Azure App Service**
```bash
# Using Azure CLI
az webapp up \
    --name your-rfp-bom-app \
    --resource-group your-resource-group \
    --runtime "PYTHON:3.9"
```

### **3. Configure App Settings**
```bash
# Set environment variables
az webapp config appsettings set \
    --name your-rfp-bom-app \
    --resource-group your-resource-group \
    --settings \
    AZURE_OPENAI_API_KEY="your-api-key" \
    AZURE_OPENAI_ENDPOINT="your-endpoint" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini" \
    AZURE_STORAGE_CONNECTION_STRING="your-connection-string" \
    SECRET_KEY="your-production-secret-key"
```

## 💰 **Cost Considerations**

### **Azure Blob Storage Pricing (Approximate)**
- **Storage**: $0.018 per GB per month
- **Transactions**: $0.0004 per 10,000 operations
- **Data Transfer**: First 5GB free per month

### **Example Monthly Costs:**
- **Small Usage** (100 users, 1GB data): ~$2-5/month
- **Medium Usage** (1000 users, 10GB data): ~$20-30/month
- **Large Usage** (10000 users, 100GB data): ~$200-300/month

## 🔒 **Security Features**

### **Data Isolation**
- Each user session gets unique folder
- No cross-user data access
- Automatic session expiry (24 hours)

### **Access Control**
- Session-based authentication
- Secure file upload validation
- Encrypted storage in Azure

### **Privacy**
- User data automatically expires
- No permanent storage of sensitive data
- GDPR-compliant data handling

## 🧪 **Testing the Storage System**

### **Local Testing with Azure Storage**
1. Set up Azure Storage Account
2. Add connection string to `.env`
3. Test file upload/download
4. Verify session isolation

### **Production Testing**
1. Deploy to Azure App Service
2. Test with multiple users
3. Verify data persistence
4. Test session expiry

## 📊 **Monitoring and Maintenance**

### **Azure Monitor Integration**
- Track storage usage
- Monitor API calls
- Set up alerts for errors

### **Cleanup Strategies**
- Automatic session expiry
- Periodic cleanup of old files
- Storage usage monitoring

## 🔄 **Fallback Strategy**

The application includes automatic fallback:
1. **Primary**: Azure Blob Storage
2. **Fallback**: Local storage (development only)
3. **Graceful Degradation**: App continues working

## 📞 **Support and Troubleshooting**

### **Common Issues**
1. **Connection String**: Verify Azure Storage configuration
2. **Permissions**: Check storage account access
3. **Session Issues**: Clear browser cookies
4. **File Size**: Check upload limits (16MB default)

### **Debug Endpoints**
- `/health` - Check system status
- `/session-info` - View session and storage info
- `/clear-session` - Reset user session

This deployment strategy ensures your RFP BOM Generator works reliably in production with proper data persistence and multi-user support! 🎯
