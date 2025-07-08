# AI-Powered RFP BOM Generator

An intelligent chatbot application that processes Request for Proposal (RFP) items using Azure OpenAI and generates accurate Bill of Materials (BOM) through fuzzy matching against stock master files.

## 🎯 Features

- **AI-Powered RFP Interpretation**: Uses Azure OpenAI GPT-4 to intelligently parse and understand RFP line items
- **Bucket-Based Filtering**: 11-bucket prioritized search strategy for accurate product matching
- **Fuzzy Matching**: Handles variations in specifications and naming conventions
- **Categorized BOM Output**: Separates matched, unmatched, and unavailable items
- **Excel Export**: Generate comprehensive BOM reports with detailed analysis
- **Interactive Chat Interface**: Built-in AI assistant for user guidance
- **Responsive Design**: Modern UI with e21c15 theme colors

## 🏗️ Architecture

| Layer          | Technology                    |
| -------------- | ----------------------------- |
| 👨‍💻 Frontend | HTML, CSS, JavaScript         |
| 🧠 AI Engine   | Azure OpenAI (GPT-4)          |
| ⚙️ Backend     | Python Flask                   |
| 📦 Storage     | Local JSON / Azure Blob        |
| 🔐 Deployment  | Azure App Service              |

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Azure OpenAI API access
- Modern web browser

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd rfp-azure
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Update the `.env` file with your Azure OpenAI credentials:
   ```env
   AZURE_OPENAI_API_KEY=your-api-key-here
   AZURE_OPENAI_ENDPOINT=your-endpoint-here
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   
   Open your browser and navigate to: `http://localhost:5000`

## 📋 Usage Guide

### Step 1: Upload Stock Master File

1. Prepare your stock master file in Excel (.xlsx, .xls) or CSV format
2. Required columns (flexible naming):
   - Product Code / Item Code
   - Description
   - Material (optional)
   - Size (optional)
   - On Hand Quantity (optional)
   - Unit Price (optional)

3. Use the provided `sample_stock_master.csv` as a reference

### Step 2: Enter RFP Line Items

Enter your RFP items one per line, for example:
```
6" SCH40 SMLS PIPE API 5L X52 PSL2
4" 150# WNRF FLANGE A105
90D LR ELBOW 6" SCH40 A234 WPB
6" X 4" CONC REDUCER SCH40 A234 WPB
```

### Step 3: Review Results

The system will categorize results into:
- **Matched**: Items successfully matched with high confidence
- **Unmatched**: Items that couldn't be matched
- **Unavailable**: Matched items with zero stock

### Step 4: Export BOM

Download the comprehensive Excel report containing:
- Detailed BOM with match scores
- Summary statistics
- Matched items sheet
- Unmatched items for review

## 🧩 Bucket-Based Search Strategy

The AI uses an 11-bucket prioritized filtering system:

| Priority | Bucket | Examples |
|----------|--------|----------|
| **High** | 1. Class Rating | 150#, 300#, 600# |
| **High** | 2. Item Group | Pipe, Flange, Elbow, Tee |
| **High** | 3. Flange Type | RF, FF, WNRF, BLRF |
| **High** | 4. Ends/Finish | NPT, SW, BW, Threaded |
| **High** | 5. Elbow Type | 90D, 45D, LR, SR |
| **High** | 6. Item Type | Equal, Reducing, Concentric |
| **Medium** | 7. Material | SS304, A105, X52, A234 WPB |
| **Medium** | 8. Thickness | SCH40, XS, STD, 7.11MM |
| **Low** | 9. Size 1 | 6", 4", DN100, NB150 |
| **Low** | 10. Size 2 | Secondary size for reducers |
| **Low** | 11. Misc | API, PSL1, Type A/B/C |

## 🔧 Configuration

### Azure OpenAI Settings

```env
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

### Matching Thresholds

Adjust confidence thresholds in `services/rfp_processor.py`:
```python
self.high_confidence_threshold = 80
self.medium_confidence_threshold = 60
self.low_confidence_threshold = 40
```

## 📊 Sample RFP Items for Testing

```
6" SCH40 SMLS PIPE API 5L X52 PSL2
4" 150# WNRF FLANGE A105
90D LR ELBOW 6" SCH40 A234 WPB
6" X 4" CONC REDUCER SCH40 A234 WPB
6" CAP SCH40 A234 WPB
NB 6.0 7.11MM SMLS PIPE
DN100 STD a234 90 degree long radius
4 INCH 150 POUND WELD NECK RAISED FACE FLANGE
```

## 🎨 UI Theme

The application uses the specified e21c15 color scheme:
- **Header Text**: #e21c15 (red)
- **Background**: #ffffff (white)
- **Accent Colors**: Complementary grays and status colors

## 🔍 API Endpoints

- `GET /` - Main application interface
- `POST /upload-stock-master` - Upload stock master file
- `POST /process-rfp` - Process RFP line items
- `POST /export-bom` - Export BOM to Excel
- `GET /health` - Health check endpoint

## 🧪 Testing

Run the application and test with the provided sample data:

1. Upload `sample_stock_master.csv`
2. Enter sample RFP items
3. Verify AI matching accuracy
4. Test Excel export functionality

## 🚀 Deployment

### Azure App Service

1. Create Azure App Service
2. Configure environment variables
3. Deploy using Git or ZIP deployment
4. Ensure Azure OpenAI access

### Docker (Optional)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the built-in chat assistant
2. Review the health endpoint: `/health`
3. Check application logs
4. Verify Azure OpenAI connectivity

## 🔮 Future Enhancements

- [ ] Advanced material specification matching
- [ ] Multi-language support
- [ ] Integration with ERP systems
- [ ] Machine learning model training
- [ ] Advanced analytics dashboard
- [ ] Mobile application support
