from flask import Flask, render_template, request, jsonify, send_file, session
import os
import json
import pandas as pd
from datetime import timedelta
from dotenv import load_dotenv
from services.azure_openai_service import AzureOpenAIService
from services.rfp_processor import RFPProcessor
from services.stock_master_service import StockMasterService
from services.rfp_file_processor import RFPFileProcessor
from services.azure_storage_service import AzureStorageService
from services.session_service import SessionService
from utils.bucket_filters import BucketFilters
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Initialize services
azure_openai_service = AzureOpenAIService()
azure_storage_service = AzureStorageService()
session_service = SessionService()
stock_master_service = StockMasterService(azure_storage_service, session_service)
rfp_file_processor = RFPFileProcessor()
rfp_processor = RFPProcessor(azure_openai_service, stock_master_service)

@app.route('/')
def index():
    """Main chatbot interface"""
    # Initialize session
    session_id = session_service.get_or_create_session_id()
    logger.info(f"User session: {session_id}")
    return render_template('index.html')

@app.route('/upload-stock-master', methods=['POST'])
def upload_stock_master():
    """Upload and process stock master file"""
    try:
        logger.info("Stock master upload request received")

        if 'file' not in request.files:
            logger.error("No file in request")
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        logger.info(f"File received: {file.filename}")

        if file.filename == '':
            logger.error("Empty filename")
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            logger.error(f"Invalid file format: {file.filename}")
            return jsonify({'error': 'Invalid file format. Please upload Excel or CSV file'}), 400

        # Process the uploaded file
        logger.info("Starting file processing...")
        result = stock_master_service.upload_stock_master(file)
        logger.info(f"File processing completed: {result}")

        return jsonify({
            'success': True,
            'message': f'Stock master file uploaded successfully. {result["total_records"]} records loaded.',
            'total_records': result['total_records'],
            'original_rows': result.get('original_rows', 0),
            'columns_found': result.get('columns_found', []),
            'mapped_columns': result.get('mapped_columns', {}),
            'sample_record': result.get('sample_record', None)
        })

    except Exception as e:
        logger.error(f"Error uploading stock master: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500

@app.route('/upload-rfp-file', methods=['POST'])
def upload_rfp_file():
    """Upload and process RFP file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Check file extension
        allowed_extensions = ['.xlsx', '.xls', '.csv', '.pdf', '.docx', '.txt']
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Invalid file format. Supported formats: {", ".join(allowed_extensions)}'}), 400

        # Process the RFP file
        result = rfp_file_processor.process_rfp_file(file)

        return jsonify({
            'success': True,
            'message': f'RFP file processed successfully. {result["total_items"]} items extracted.',
            'total_items': result['total_items'],
            'rfp_items': result['rfp_items'],
            'file_type': result['file_type'],
            'original_filename': result['original_filename']
        })

    except Exception as e:
        logger.error(f"Error processing RFP file: {str(e)}")
        return jsonify({'error': f'Failed to process RFP file: {str(e)}'}), 500

@app.route('/process-rfp', methods=['POST'])
def process_rfp():
    """Process RFP line items and generate BOM"""
    try:
        data = request.get_json()
        rfp_items = data.get('rfp_items', [])

        if not rfp_items:
            return jsonify({'error': 'No RFP items provided'}), 400

        if not stock_master_service.has_stock_data():
            return jsonify({'error': 'Please upload stock master file first'}), 400

        # Process RFP items
        results = rfp_processor.process_rfp_items(rfp_items)

        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_items': len(rfp_items),
                'matched': len([r for r in results if r['status'] == 'matched']),
                'unmatched': len([r for r in results if r['status'] == 'unmatched']),
                'unavailable': len([r for r in results if r['status'] == 'unavailable'])
            }
        })

    except Exception as e:
        logger.error(f"Error processing RFP: {str(e)}")
        return jsonify({'error': f'Failed to process RFP: {str(e)}'}), 500

@app.route('/export-bom', methods=['POST'])
def export_bom():
    """Export BOM to Excel file"""
    try:
        data = request.get_json()
        bom_data = data.get('bom_data', [])
        
        if not bom_data:
            return jsonify({'error': 'No BOM data provided'}), 400
        
        # Generate Excel file
        file_path = rfp_processor.export_bom_to_excel(bom_data)
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name='generated_bom.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error exporting BOM: {str(e)}")
        return jsonify({'error': f'Failed to export BOM: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    session_id = session_service.get_or_create_session_id()
    return jsonify({
        'status': 'healthy',
        'azure_openai': azure_openai_service.test_connection(),
        'stock_master_loaded': session_service.has_stock_master(),
        'session_info': session_service.get_session_info(),
        'storage_info': azure_storage_service.get_storage_info()
    })

@app.route('/session-info')
def session_info():
    """Get session and storage information"""
    return jsonify({
        'session': session_service.get_session_info(),
        'storage': azure_storage_service.get_storage_info(),
        'stock_master': session_service.get_stock_master_info()
    })

@app.route('/clear-session', methods=['POST'])
def clear_session():
    """Clear current session and data"""
    try:
        session_id = session_service.get_session_id()
        if session_id:
            # Optionally delete user files from storage
            # azure_storage_service.delete_user_data(session_id)
            pass

        session_service.clear_session()
        return jsonify({'success': True, 'message': 'Session cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        return jsonify({'error': f'Failed to clear session: {str(e)}'}), 500

@app.route('/debug-stock-sample')
def debug_stock_sample():
    """Debug endpoint to check stock data sample"""
    try:
        # Load session stock data
        stock_master_service._try_load_session_data()
        stock_data = stock_master_service.get_stock_data()

        if not stock_data:
            return jsonify({'error': 'No stock data loaded'})

        # Return sample of stock data for debugging
        sample_size = min(10, len(stock_data))
        sample_data = stock_data[:sample_size]

        # Get all unique keys from the first few records to see field structure
        all_keys = set()
        for item in stock_data[:5]:
            all_keys.update(item.keys())

        # Get unique categories to see diversity
        all_categories = set()
        for item in stock_data:
            cat = item.get('main_category', 'N/A')
            if cat and cat != 'N/A':
                all_categories.add(cat)

        return jsonify({
            'total_records': len(stock_data),
            'sample_records': sample_data,
            'first_product_code': stock_data[0].get('product_code', 'N/A') if stock_data else 'N/A',
            'categories_sample': [item.get('main_category', 'N/A') for item in stock_data[:5]],
            'unique_categories': sorted(list(all_categories)),
            'category_count': len(all_categories),
            'all_fields': sorted(list(all_keys)),
            'field_analysis': {
                'has_main_category': any('main_category' in item for item in stock_data[:10]),
                'has_maincategory': any('maincategory' in item for item in stock_data[:10]),
                'has_category': any('category' in item for item in stock_data[:10])
            }
        })
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/debug-ai-config')
def debug_ai_config():
    """Debug endpoint to check Azure OpenAI configuration"""
    try:
        # Get AI service configuration
        ai_config = {
            'api_key_configured': bool(azure_openai_service.api_key),
            'endpoint': azure_openai_service.endpoint,
            'api_version': azure_openai_service.api_version,
            'deployment_name': azure_openai_service.deployment_name,
            'use_mock': azure_openai_service.use_mock,
            'client_initialized': azure_openai_service.client is not None
        }

        # Test connection
        connection_test = azure_openai_service.test_connection()

        # Test a simple AI call
        test_result = None
        test_error = None
        try:
            if not azure_openai_service.use_mock:
                test_response = azure_openai_service.client.chat.completions.create(
                    model=azure_openai_service.deployment_name,
                    messages=[{"role": "user", "content": "Say 'AI is working'"}],
                    max_tokens=10
                )
                test_result = test_response.choices[0].message.content
            else:
                test_result = "Using mock responses"
        except Exception as e:
            test_error = str(e)

        return jsonify({
            'ai_configuration': ai_config,
            'connection_test': connection_test,
            'simple_test_result': test_result,
            'simple_test_error': test_error,
            'environment_variables': {
                'AZURE_OPENAI_API_KEY': 'Set' if os.getenv('AZURE_OPENAI_API_KEY') else 'Missing',
                'AZURE_OPENAI_ENDPOINT': os.getenv('AZURE_OPENAI_ENDPOINT', 'Missing'),
                'AZURE_OPENAI_DEPLOYMENT_NAME': os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'Missing'),
                'AZURE_OPENAI_API_VERSION': os.getenv('AZURE_OPENAI_API_VERSION', 'Missing')
            }
        })
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
