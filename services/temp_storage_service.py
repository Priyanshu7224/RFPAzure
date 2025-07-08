import os
import json
import tempfile
import logging
from typing import Dict, List, Optional
from flask import session

logger = logging.getLogger(__name__)

class TempStorageService:
    """
    Temporary storage service for Azure App Services
    Uses session storage for small data and temp files for uploads
    WARNING: This is a temporary solution - use Azure Blob Storage for production
    """
    
    def __init__(self):
        self.max_session_size = 1024 * 1024  # 1MB max in session
    
    def store_stock_data(self, stock_data: List[Dict]) -> bool:
        """Store stock data in session if small enough"""
        try:
            # Convert to JSON to check size
            json_data = json.dumps(stock_data)
            
            if len(json_data.encode('utf-8')) < self.max_session_size:
                # Store in session
                session['stock_data'] = stock_data
                session['stock_data_size'] = len(stock_data)
                logger.info(f"Stored {len(stock_data)} records in session")
                return True
            else:
                # Too large for session storage
                logger.warning(f"Stock data too large for session storage: {len(json_data)} bytes")
                return False
                
        except Exception as e:
            logger.error(f"Failed to store stock data: {e}")
            return False
    
    def get_stock_data(self) -> List[Dict]:
        """Get stock data from session"""
        return session.get('stock_data', [])
    
    def has_stock_data(self) -> bool:
        """Check if stock data exists in session"""
        return 'stock_data' in session and len(session.get('stock_data', [])) > 0
    
    def clear_stock_data(self):
        """Clear stock data from session"""
        session.pop('stock_data', None)
        session.pop('stock_data_size', None)
    
    def get_stock_info(self) -> Dict:
        """Get stock data information"""
        stock_data = session.get('stock_data', [])
        return {
            'has_data': len(stock_data) > 0,
            'record_count': len(stock_data),
            'storage_type': 'session',
            'size_limit': self.max_session_size
        }
    
    def create_temp_file(self, content: bytes, suffix: str = '.tmp') -> str:
        """Create temporary file for processing"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name
    
    def cleanup_temp_file(self, filepath: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            logger.error(f"Failed to cleanup temp file {filepath}: {e}")
