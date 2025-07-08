import os
import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from utils.bucket_filters import BucketFilters
from services.azure_openai_service import AzureOpenAIService
from services.stock_master_service import StockMasterService

logger = logging.getLogger(__name__)

class RFPProcessor:
    """Core engine for processing RFP line items and generating BOM"""
    
    def __init__(self, azure_openai_service: AzureOpenAIService, stock_master_service: StockMasterService):
        self.azure_openai_service = azure_openai_service
        self.stock_master_service = stock_master_service
        self.bucket_filters = BucketFilters()
        
        # Thresholds for matching
        self.high_confidence_threshold = 80
        self.medium_confidence_threshold = 60
        self.low_confidence_threshold = 40
    
    def process_rfp_items(self, rfp_items: List[str]) -> List[Dict[str, Any]]:
        """
        Process a list of RFP line items and generate BOM
        
        Args:
            rfp_items: List of RFP line item descriptions
            
        Returns:
            List of processed results with matches
        """
        results = []
        
        for i, rfp_item in enumerate(rfp_items):
            logger.info(f"Processing RFP item {i+1}/{len(rfp_items)}: {rfp_item[:50]}...")
            
            try:
                result = self.process_single_rfp_item(rfp_item)
                result['line_number'] = i + 1
                result['original_rfp_item'] = rfp_item
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing RFP item {i+1}: {str(e)}")
                results.append({
                    'line_number': i + 1,
                    'original_rfp_item': rfp_item,
                    'status': 'error',
                    'error_message': str(e),
                    'matched_product_code': '',
                    'matched_description': '',
                    'match_score': 0,
                    'match_reason': f'Processing error: {str(e)}'
                })
        
        return results
    
    def process_single_rfp_item(self, rfp_item: str) -> Dict[str, Any]:
        """
        Process a single RFP line item
        
        Args:
            rfp_item: RFP line item description
            
        Returns:
            Dict with processing results
        """
        # Step 1: Extract bucket features from RFP item
        rfp_features = self.bucket_filters.extract_bucket_features(rfp_item)
        
        # Step 2: Filter stock data using bucket-based approach
        stock_data = self.stock_master_service.get_stock_data()
        filtered_stock = self.bucket_filters.filter_stock_by_buckets(
            rfp_features, stock_data, max_results=20
        )
        
        if not filtered_stock:
            return {
                'status': 'unmatched',
                'matched_product_code': '',
                'matched_description': '',
                'match_score': 0,
                'on_hand_quantity': 0,
                'match_reason': 'No matching products found in stock master using bucket filtering',
                'bucket_features': rfp_features,
                'filtered_candidates': 0
            }
        
        # Step 3: Use Azure OpenAI for intelligent matching
        ai_result = self.azure_openai_service.match_rfp_item(rfp_item, filtered_stock)
        
        # Step 4: Validate and enhance the AI result
        enhanced_result = self._enhance_ai_result(ai_result, filtered_stock, rfp_features)
        
        return enhanced_result
    
    def _enhance_ai_result(self, ai_result: Dict, filtered_stock: List[Dict], 
                          rfp_features: Dict) -> Dict[str, Any]:
        """
        Enhance and validate AI matching result
        
        Args:
            ai_result: Result from Azure OpenAI
            filtered_stock: Filtered stock candidates
            rfp_features: Extracted RFP features
            
        Returns:
            Enhanced result dictionary
        """
        try:
            match_score = float(ai_result.get('match_score', 0))
            product_code = ai_result.get('matched_product_code', '')
            
            # Find the matched stock item for additional details
            matched_stock_item = None
            if product_code:
                matched_stock_item = next(
                    (item for item in filtered_stock if item.get('product_code') == product_code),
                    None
                )
            
            # Determine status based on match score and availability
            status = self._determine_match_status(match_score, matched_stock_item)
            
            # Get quantity information
            on_hand_quantity = 0
            if matched_stock_item:
                try:
                    qty_str = matched_stock_item.get('on_hand_quantity', '0')
                    on_hand_quantity = float(qty_str) if qty_str else 0
                except (ValueError, TypeError):
                    on_hand_quantity = 0
            
            return {
                'status': status,
                'matched_product_code': product_code,
                'matched_description': ai_result.get('matched_description', ''),
                'match_score': match_score,
                'on_hand_quantity': on_hand_quantity,
                'match_reason': ai_result.get('match_reason', ''),
                'bucket_features': rfp_features,
                'filtered_candidates': len(filtered_stock),
                'confidence_level': self._get_confidence_level(match_score),
                'matched_stock_details': matched_stock_item,
                'alternative_matches': [
                    {
                        'product_code': item.get('product_code', ''),
                        'description': item.get('description', ''),
                        'bucket_score': item.get('match_score', 0)
                    }
                    for item in filtered_stock[:3] if item.get('product_code') != product_code
                ]
            }
            
        except Exception as e:
            logger.error(f"Error enhancing AI result: {str(e)}")
            return {
                'status': 'error',
                'matched_product_code': '',
                'matched_description': '',
                'match_score': 0,
                'on_hand_quantity': 0,
                'match_reason': f'Error processing AI result: {str(e)}',
                'bucket_features': rfp_features,
                'filtered_candidates': len(filtered_stock)
            }
    
    def _determine_match_status(self, match_score: float, stock_item: Dict) -> str:
        """Determine the status of the match"""
        if match_score < self.low_confidence_threshold:
            return 'unmatched'
        
        if not stock_item:
            return 'unmatched'
        
        # Check availability
        try:
            qty_str = stock_item.get('on_hand_quantity', '0')
            quantity = float(qty_str) if qty_str else 0
            if quantity <= 0:
                return 'unavailable'
        except (ValueError, TypeError):
            pass  # Assume available if quantity is unclear
        
        return 'matched'
    
    def _get_confidence_level(self, match_score: float) -> str:
        """Get confidence level based on match score"""
        if match_score >= self.high_confidence_threshold:
            return 'high'
        elif match_score >= self.medium_confidence_threshold:
            return 'medium'
        elif match_score >= self.low_confidence_threshold:
            return 'low'
        else:
            return 'very_low'
    
    def export_bom_to_excel(self, bom_data: List[Dict]) -> str:
        """
        Export BOM data to Excel file
        
        Args:
            bom_data: List of BOM items
            
        Returns:
            Path to generated Excel file
        """
        try:
            # Prepare data for Excel export
            export_data = []
            
            for item in bom_data:
                export_data.append({
                    'Line Number': item.get('line_number', ''),
                    'Original RFP Item': item.get('original_rfp_item', ''),
                    'Status': item.get('status', '').upper(),
                    'Matched Product Code': item.get('matched_product_code', ''),
                    'Matched Description': item.get('matched_description', ''),
                    'Match Score': item.get('match_score', 0),
                    'Confidence Level': item.get('confidence_level', '').upper(),
                    'On Hand Quantity': item.get('on_hand_quantity', 0),
                    'Match Reason': item.get('match_reason', ''),
                    'Alternative Matches': '; '.join([
                        f"{alt.get('product_code', '')} ({alt.get('bucket_score', 0):.1f})"
                        for alt in item.get('alternative_matches', [])
                    ])
                })
            
            # Create DataFrame
            df = pd.DataFrame(export_data)
            
            # Create exports directory if it doesn't exist
            exports_dir = 'exports'
            if not os.path.exists(exports_dir):
                os.makedirs(exports_dir)
                logger.info(f"Created exports directory: {exports_dir}")

            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'BOM_Export_{timestamp}.xlsx'
            file_path = os.path.join(exports_dir, filename)
            
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                # Main BOM sheet
                df.to_excel(writer, sheet_name='BOM', index=False)
                
                # Summary sheet
                summary_data = self._generate_bom_summary(bom_data)
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Matched items sheet
                matched_items = [item for item in bom_data if item.get('status') == 'matched']
                if matched_items:
                    matched_df = pd.DataFrame([{
                        'Product Code': item.get('matched_product_code', ''),
                        'Description': item.get('matched_description', ''),
                        'Quantity': item.get('on_hand_quantity', 0),
                        'Match Score': item.get('match_score', 0)
                    } for item in matched_items])
                    matched_df.to_excel(writer, sheet_name='Matched Items', index=False)
                
                # Unmatched items sheet
                unmatched_items = [item for item in bom_data if item.get('status') in ['unmatched', 'unavailable']]
                if unmatched_items:
                    unmatched_df = pd.DataFrame([{
                        'Original RFP Item': item.get('original_rfp_item', ''),
                        'Status': item.get('status', ''),
                        'Reason': item.get('match_reason', '')
                    } for item in unmatched_items])
                    unmatched_df.to_excel(writer, sheet_name='Unmatched Items', index=False)
            
            logger.info(f"BOM exported to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error exporting BOM to Excel: {str(e)}")
            raise e
    
    def _generate_bom_summary(self, bom_data: List[Dict]) -> List[Dict]:
        """Generate summary statistics for BOM"""
        total_items = len(bom_data)
        matched = len([item for item in bom_data if item.get('status') == 'matched'])
        unmatched = len([item for item in bom_data if item.get('status') == 'unmatched'])
        unavailable = len([item for item in bom_data if item.get('status') == 'unavailable'])
        errors = len([item for item in bom_data if item.get('status') == 'error'])
        
        # Confidence level breakdown
        high_conf = len([item for item in bom_data if item.get('confidence_level') == 'high'])
        medium_conf = len([item for item in bom_data if item.get('confidence_level') == 'medium'])
        low_conf = len([item for item in bom_data if item.get('confidence_level') == 'low'])
        
        return [
            {'Metric': 'Total Items', 'Count': total_items, 'Percentage': '100.0%'},
            {'Metric': 'Matched Items', 'Count': matched, 'Percentage': f'{(matched/total_items*100):.1f}%' if total_items > 0 else '0.0%'},
            {'Metric': 'Unmatched Items', 'Count': unmatched, 'Percentage': f'{(unmatched/total_items*100):.1f}%' if total_items > 0 else '0.0%'},
            {'Metric': 'Unavailable Items', 'Count': unavailable, 'Percentage': f'{(unavailable/total_items*100):.1f}%' if total_items > 0 else '0.0%'},
            {'Metric': 'Processing Errors', 'Count': errors, 'Percentage': f'{(errors/total_items*100):.1f}%' if total_items > 0 else '0.0%'},
            {'Metric': 'High Confidence Matches', 'Count': high_conf, 'Percentage': f'{(high_conf/total_items*100):.1f}%' if total_items > 0 else '0.0%'},
            {'Metric': 'Medium Confidence Matches', 'Count': medium_conf, 'Percentage': f'{(medium_conf/total_items*100):.1f}%' if total_items > 0 else '0.0%'},
            {'Metric': 'Low Confidence Matches', 'Count': low_conf, 'Percentage': f'{(low_conf/total_items*100):.1f}%' if total_items > 0 else '0.0%'}
        ]
