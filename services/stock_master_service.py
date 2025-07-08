import os
import pandas as pd
import json
import logging
import tempfile
from typing import Dict, List, Optional
from werkzeug.datastructures import FileStorage
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class StockMasterService:
    """Service for managing stock master file operations"""

    def __init__(self, azure_storage_service=None, session_service=None):
        self.azure_storage_service = azure_storage_service
        self.session_service = session_service
        self.stock_data: List[Dict] = []
        self.current_session_stock_blob = None

        # Note: Session data will be loaded when needed in request context
    
    def load_session_stock_data(self):
        """Load existing stock data for current session"""
        try:
            if self.session_service and self.azure_storage_service:
                stock_info = self.session_service.get_stock_master_info()
                if stock_info and stock_info['blob_name']:
                    data = self.azure_storage_service.load_json_data(stock_info['blob_name'])
                    if data and 'stock_data' in data:
                        self.stock_data = data['stock_data']
                        self.current_session_stock_blob = stock_info['blob_name']
                        logger.info(f"Loaded {len(self.stock_data)} stock records from session storage")
        except Exception as e:
            logger.error(f"Error loading session stock data: {str(e)}")
            self.stock_data = []
    
    def upload_stock_master(self, file: FileStorage) -> Dict:
        """
        Upload and process stock master file

        Args:
            file: Uploaded file (Excel or CSV)

        Returns:
            Dict with upload results
        """
        try:
            # Create temporary file for processing (Azure App Services compatible)
            file_extension = os.path.splitext(file.filename)[1]
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
            temp_file_path = temp_file.name

            # Save uploaded file to temporary location
            file.save(temp_file_path)
            temp_file.close()

            logger.info(f"Processing file: {file.filename}, size: {os.path.getsize(temp_file_path)} bytes")

            # Read the file based on extension with better error handling
            df = None
            if file.filename.lower().endswith('.csv'):
                # Try different encodings for CSV files
                for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(temp_file_path, encoding=encoding)
                        logger.info(f"Successfully read CSV with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                if df is None:
                    raise ValueError("Could not read CSV file with any supported encoding")
            else:
                # Handle Excel files
                try:
                    df = pd.read_excel(temp_file_path, engine='openpyxl')
                except Exception as e:
                    logger.warning(f"Failed with openpyxl, trying xlrd: {e}")
                    df = pd.read_excel(temp_file_path, engine='xlrd')

            logger.info(f"Raw dataframe shape: {df.shape}")
            logger.info(f"Original columns: {list(df.columns)}")

            # Remove completely empty rows
            df = df.dropna(how='all')
            logger.info(f"After removing empty rows: {df.shape}")

            # Clean and standardize column names
            df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')
            logger.info(f"Cleaned columns: {list(df.columns)}")

            # Expected columns (flexible mapping) - Updated for user's file structure
            column_mapping = {
                'product_code': ['prd_code', 'product_code', 'item_code', 'code', 'part_number', 'part_no', 'partno', 'item_no', 'itemno', 'product_id'],
                'description': ['prd_desc1', 'prd_desc2', 'maindesc', 'description', 'item_description', 'desc', 'product_description', 'item_desc', 'product_desc', 'name', 'item_name'],
                'main_category': ['maincategory', 'main_category', 'category', 'product_category', 'item_category', 'type', 'product_type', 'class', 'group'],
                'material': ['material', 'material_grade', 'grade', 'material_spec', 'mat', 'material_type'],
                'size': ['size', 'nominal_size', 'pipe_size', 'diameter', 'dim', 'dimension'],
                'specification': ['specification', 'spec', 'standard', 'norm', 'std'],
                'on_hand_quantity': ['onhand', 'on_hand_quantity', 'quantity', 'qty', 'stock_qty', 'available_qty', 'stock', 'inventory', 'balance'],
                'unit_price': ['unit_price', 'price', 'cost', 'rate', 'unit_cost'],
                'unit': ['uom', 'unit', 'unit_of_measure', 'units'],
                'alt_product_1': ['alt_prd1', 'alt_product_1', 'alternative_1'],
                'alt_product_2': ['alt_prd2', 'alt_product_2', 'alternative_2'],
                'alt_product_3': ['alt_prd3', 'alt_product_3', 'alternative_3']
            }

            # Map columns to standard names
            standardized_data = []
            mapped_columns = {}

            # First, identify which columns map to which standard fields
            for standard_col, possible_cols in column_mapping.items():
                for col in possible_cols:
                    if col in df.columns:
                        mapped_columns[standard_col] = col
                        break

            logger.info(f"Column mapping: {mapped_columns}")

            # Process each row
            for idx, row in df.iterrows():
                record = {}
                for standard_col, possible_cols in column_mapping.items():
                    value = ""
                    if standard_col in mapped_columns:
                        col_name = mapped_columns[standard_col]
                        if pd.notna(row[col_name]):
                            value = str(row[col_name]).strip()
                    record[standard_col] = value

                # Special handling for description - combine Prd_Desc1 and Prd_Desc2 if both exist
                if 'prd_desc1' in df.columns and 'prd_desc2' in df.columns:
                    desc1 = str(row['prd_desc1']).strip() if pd.notna(row['prd_desc1']) else ""
                    desc2 = str(row['prd_desc2']).strip() if pd.notna(row['prd_desc2']) else ""

                    # Combine descriptions
                    combined_desc = []
                    if desc1:
                        combined_desc.append(desc1)
                    if desc2:
                        combined_desc.append(desc2)

                    if combined_desc:
                        record['description'] = " | ".join(combined_desc)

                # Add MainDesc if available and description is still empty
                if not record['description'] and 'maindesc' in df.columns and pd.notna(row['maindesc']):
                    record['description'] = str(row['maindesc']).strip()

                # Debug: Log first few records
                if idx < 3:
                    logger.info(f"Row {idx}: {record}")

                # Only add records with at least product code OR description
                if record['product_code'] or record['description']:
                    # If product code is missing but description exists, use row index as code
                    if not record['product_code'] and record['description']:
                        record['product_code'] = f"ITEM_{idx+1:06d}"
                    standardized_data.append(record)
                elif idx < 5:  # Log why first few records were rejected
                    logger.warning(f"Row {idx} rejected - no product_code or description: {record}")

            logger.info(f"Processed {len(standardized_data)} valid records")

            # Update stock data
            self.stock_data = standardized_data

            # Save to storage (Azure Blob or local)
            if self.azure_storage_service and self.session_service:
                session_id = self.session_service.get_or_create_session_id()

                # Prepare data for storage
                storage_data = {
                    'stock_data': self.stock_data,
                    'metadata': {
                        'original_filename': file.filename,
                        'upload_timestamp': datetime.now().isoformat(),
                        'total_records': len(self.stock_data),
                        'original_rows': len(df),
                        'columns_found': list(df.columns),
                        'mapped_columns': mapped_columns
                    }
                }

                # Save to storage
                blob_name = self.azure_storage_service.save_json_data(storage_data, session_id, 'stock_master')
                self.current_session_stock_blob = blob_name

                # Update session
                self.session_service.set_stock_master_uploaded(blob_name, len(self.stock_data))

                logger.info(f"Saved stock data to storage: {blob_name}")
            else:
                # Fallback to local storage
                local_file_path = os.path.join('uploads', 'stock_master.json')
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                with open(local_file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.stock_data, f, indent=2, ensure_ascii=False)

            # Clean up temporary file
            os.remove(temp_file_path)

            logger.info(f"Successfully processed stock master file: {len(self.stock_data)} records")

            return {
                'success': True,
                'total_records': len(self.stock_data),
                'original_rows': len(df),
                'columns_found': list(df.columns),
                'mapped_columns': mapped_columns,
                'sample_record': self.stock_data[0] if self.stock_data else None
            }

        except Exception as e:
            logger.error(f"Error processing stock master file: {str(e)}")
            # Clean up temporary file if it exists
            temp_file_path = os.path.join('uploads', f"temp_{file.filename}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise e
    
    def get_stock_data(self) -> List[Dict]:
        """Get all stock data"""
        return self.stock_data
    
    def search_stock(self, query: str, limit: int = 100) -> List[Dict]:
        """
        Search stock data by query string
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching stock records
        """
        if not self.stock_data:
            return []
        
        query_lower = query.lower()
        results = []
        
        for record in self.stock_data:
            # Search in key fields
            searchable_text = ' '.join([
                record.get('product_code', ''),
                record.get('description', ''),
                record.get('material', ''),
                record.get('size', ''),
                record.get('specification', '')
            ]).lower()
            
            if query_lower in searchable_text:
                results.append(record)
                
            if len(results) >= limit:
                break
        
        return results
    
    def get_stock_by_code(self, product_code: str) -> Optional[Dict]:
        """Get stock record by product code"""
        for record in self.stock_data:
            if record.get('product_code', '').upper() == product_code.upper():
                return record
        return None
    
    def has_stock_data(self) -> bool:
        """Check if stock data is loaded"""
        # Try to load session data if not already loaded
        if len(self.stock_data) == 0:
            self._try_load_session_data()
        return len(self.stock_data) > 0

    def _try_load_session_data(self):
        """Try to load session data if in request context"""
        try:
            if self.session_service and self.session_service.has_stock_master():
                self.load_session_stock_data()
        except RuntimeError:
            # Not in request context, skip loading
            pass
    
    def get_stock_statistics(self) -> Dict:
        """Get statistics about loaded stock data"""
        if not self.stock_data:
            return {'total_records': 0}
        
        # Count records by category
        materials = set()
        sizes = set()
        specifications = set()
        
        for record in self.stock_data:
            if record.get('material'):
                materials.add(record['material'])
            if record.get('size'):
                sizes.add(record['size'])
            if record.get('specification'):
                specifications.add(record['specification'])
        
        return {
            'total_records': len(self.stock_data),
            'unique_materials': len(materials),
            'unique_sizes': len(sizes),
            'unique_specifications': len(specifications),
            'sample_materials': list(materials)[:10],
            'sample_sizes': list(sizes)[:10],
            'sample_specifications': list(specifications)[:10]
        }
    
    def validate_stock_data(self) -> Dict:
        """Validate the quality of stock data"""
        if not self.stock_data:
            return {'valid': False, 'errors': ['No stock data loaded']}
        
        errors = []
        warnings = []
        
        # Check for required fields
        records_without_code = sum(1 for r in self.stock_data if not r.get('product_code'))
        records_without_desc = sum(1 for r in self.stock_data if not r.get('description'))
        
        if records_without_code > 0:
            errors.append(f"{records_without_code} records missing product code")
        
        if records_without_desc > 0:
            errors.append(f"{records_without_desc} records missing description")
        
        # Check for duplicates
        codes = [r.get('product_code', '') for r in self.stock_data if r.get('product_code')]
        duplicate_codes = len(codes) - len(set(codes))
        
        if duplicate_codes > 0:
            warnings.append(f"{duplicate_codes} duplicate product codes found")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_records': len(self.stock_data)
        }
