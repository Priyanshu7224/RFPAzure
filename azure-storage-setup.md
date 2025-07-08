# Azure Storage Setup for Production

## Step 1: Create Storage Account

### Using Azure Portal:
1. Go to https://portal.azure.com
2. Click "Create a resource"
3. Search for "Storage account"
4. Fill in details:
   - **Subscription**: Your subscription
   - **Resource Group**: Same as your web app
   - **Storage Account Name**: `rfpbomstorage` (must be globally unique)
   - **Region**: Same as your web app
   - **Performance**: Standard
   - **Redundancy**: LRS (cheapest option)

### Using Azure CLI:
```bash
# Create storage account
az storage account create \
    --name rfpbomstorage \
    --resource-group your-resource-group \
    --location eastus \
    --sku Standard_LRS

# Get connection string
az storage account show-connection-string \
    --name rfpbomstorage \
    --resource-group your-resource-group \
    --query connectionString \
    --output tsv
```

## Step 2: Configure Web App

### In Azure Portal:
1. Go to your App Service
2. Navigate to "Configuration" → "Application settings"
3. Add new setting:
   - **Name**: `AZURE_STORAGE_CONNECTION_STRING`
   - **Value**: `DefaultEndpointsProtocol=https;AccountName=rfpbomstorage;AccountKey=YOUR_KEY;EndpointSuffix=core.windows.net`

### Using Azure CLI:
```bash
# Set application setting
az webapp config appsettings set \
    --name your-web-app-name \
    --resource-group your-resource-group \
    --settings AZURE_STORAGE_CONNECTION_STRING="your-connection-string"
```

## Step 3: Verify Setup

After deployment, check:
- Visit `/session-info` endpoint
- Should show "Storage Type: Azure Blob Storage"
- Upload test file to verify it works

## Cost Estimate

**Monthly costs for typical usage:**
- Storage: $0.018/GB (~$2 for 100GB)
- Transactions: $0.0004/10K operations (~$1 for 2.5M operations)
- **Total: $5-20/month for most use cases**
