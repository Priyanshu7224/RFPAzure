import re
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

class BucketFilters:
    """
    Implements the 11-bucket filtering strategy for intelligent product matching
    """
    
    def __init__(self):
        self.bucket_definitions = {
            1: {  # Class Rating
                'name': 'Class Rating',
                'priority': 'high',
                'patterns': [
                    r'\b(150|300|600|900|1500|2500|5000|3000|6000|9000)#?\b',
                    r'\b(150|300|600|900|1500|2500|5000|3000|6000|9000)\s*LB\b',
                    r'\bCLASS\s*(150|300|600|900|1500|2500|5000|3000|6000|9000)\b'
                ]
            },
            2: {  # Item Group
                'name': 'Item Group',
                'priority': 'high',
                'patterns': [
                    r'\b(PIPE|ELBOW|CAP|FLANGE|FLG|TEE|REDUCER|REDG|RED|BEND|SWAGE|COUPLING|CLPG|BOSS|UNION|NIPPLE|PLUG|CROSS|INSERT|PIPET|WELDOLET|SOCKOLET|ELBOLET|THREADOLET)\b'
                ]
            },
            3: {  # Flange Type/Facing
                'name': 'Flange Type/Facing',
                'priority': 'high',
                'patterns': [
                    r'\b(RF|RAISED\s*FACE|FF|FLAT\s*FACE|WN|WNRF|WN\s*RF|WNFF|WN\s*FF|WELDNECK|WELD\s*NECK|BLIND|BL|BLRF|BL\s*RF|BLFF|BF\s*FF|SO|SORF|SO\s*RF|SOFF|SO\s*FF|SLIP\s*ON|SLIPON|SLIP-ON|LJ|LJRF|LJ\s*RF|LJFF|LJ\s*FF|LAP\s*JOINT|LAPJOINT|LAP-JOINT)\b'
                ]
            },
            4: {  # Item Ends/Finish
                'name': 'Item Ends/Finish',
                'priority': 'high',
                'patterns': [
                    r'\b(NPT|THREADED|TH|SCRD|SCREWED|SW|SOCKET\s*WELD|SOCKETWELD|BW|BUTTWELD|SMLS|SEAMLESS|WELDED|WE)\b'
                ]
            },
            5: {  # Elbow Type
                'name': 'Elbow Type',
                'priority': 'high',
                'patterns': [
                    r'\b(LR|LONG\s*RADIUS|SR|SHORT\s*RADIUS|90LR|90SR|90|90DEG|90D|90\s*DEG|90\s*DEGREE|45LR|45SR|45|45DEG|45D|45\s*DEG|45\s*DEGREE|180LR|180SR|180|180DEG|180D|180\s*DEG|180\s*DEGREE)\b'
                ]
            },
            6: {  # Item Type
                'name': 'Item Type',
                'priority': 'high',
                'patterns': [
                    r'\b(EQ|EQUAL|ECC|ECCENTRIC|CON|CONC|CONCENTRIC|RED|REDUCING|REDG|FULL|HALF|HEX|BULL|ROUND)\b'
                ]
            },
            7: {  # Material
                'name': 'Material',
                'priority': 'medium',
                'patterns': [
                    r'\b(CS|CARBON\s*STEEL|CARBONSTEEL|SS|STAINLESS\s*STEEL|STAINLESSSTEEL|X52|X42|A53|SA/A106-B|A106-B|A106B|A106GRB|A106\s*GRB|SA/A333\s*GR\.6|A333GR6|A333\s*GR6|304|SS304|SS304/L|SS304L|316|SS316|SS316/L|SS316L|TP304/L|TP304|TP304L|TP316|TP316/L|TP316L|SA/A234\s*WPB|234WPB|A234WPB|A234|234|SA/A105N|A105|A105N|105|F304/304L|304/304L|F304/L|F304L|304L|F316/316L|316/316L|F316/L|F316L|316L|304/L|316/L|WP304/L|WP304/304L|F304/L|F304L|WP316/L|WP316/316L|F316/L|F316L)\b'
                ]
            },
            8: {  # Thickness
                'name': 'Thickness',
                'priority': 'medium',
                'patterns': [
                    r'\b(S10|S20|S30|S40|S60|S80|S100|S120|S140|S160|SSTD|SXS|SXXS|SCH\s*10|SCH\s*20|SCH\s*30|SCH\s*40|SCH\s*60|SCH\s*80|SCH\s*100|SCH\s*120|SCH\s*140|SCH\s*160|SCH\s*STD|SCH\s*XS|SCH\s*XXS|SCH10|SCH20|SCH30|SCH40|SCH60|SCH80|SCH100|SCH120|SCH140|SCH160|SCHSTD|SCHXS|SCHXXS|STD|XS|XXS)\b',
                    r'\b\d+\.?\d*\s*MM\b',  # Metric thickness
                    r'\b\d+\.?\d*\s*INCH\b'  # Imperial thickness
                ]
            },
            9: {  # Size 1
                'name': 'Size 1',
                'priority': 'low',
                'patterns': [
                    r'\b(1/8|1/4|1/2|3/4|1|1\.1/4|1\.1/2|2|2\.1/2|3|3\.1/2|4|5|6|7|8|10|12|14|16|18|20|22|24|26|28|30|32|34|36|38|40|42|44)"\b',
                    r'\bDN\s*(\d+)\b',  # Metric DN sizes
                    r'\bNB\s*(\d+\.?\d*)\b'  # Nominal bore
                ]
            },
            10: {  # Size 2
                'name': 'Size 2',
                'priority': 'low',
                'patterns': [
                    r'X\s*(1/8|1/4|1/2|3/4|1|1\.1/4|1\.1/2|2|2\.1/2|3|3\.1/2|4|5|6|7|8|10|12|14|16|18|20|22|24|26|28|30|32|34|36|38|40|42|44)"\b',
                    r'TO\s*(1/8|1/4|1/2|3/4|1|1\.1/4|1\.1/2|2|2\.1/2|3|3\.1/2|4|5|6|7|8|10|12|14|16|18|20|22|24|26|28|30|32|34|36|38|40|42|44)"\b'
                ]
            },
            11: {  # Misc
                'name': 'Misc',
                'priority': 'low',
                'patterns': [
                    r'\b(API|PSL1|PSL2|PSL3|TYPE\s*A|TYPE\s*B|TYPE\s*C)\b'
                ]
            }
        }
    
    def extract_bucket_features(self, text: str) -> Dict[int, List[str]]:
        """
        Extract features from text based on bucket definitions
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dict mapping bucket number to list of matched features
        """
        text_upper = text.upper()
        features = {}
        
        for bucket_num, bucket_def in self.bucket_definitions.items():
            matches = []
            for pattern in bucket_def['patterns']:
                found_matches = re.findall(pattern, text_upper, re.IGNORECASE)
                if found_matches:
                    if isinstance(found_matches[0], tuple):
                        # Handle groups in regex
                        matches.extend([match for group in found_matches for match in group if match])
                    else:
                        matches.extend(found_matches)
            
            if matches:
                features[bucket_num] = list(set(matches))  # Remove duplicates
        
        return features
    
    def filter_stock_by_buckets(self, rfp_features: Dict[int, List[str]], 
                               stock_data: List[Dict], 
                               max_results: int = 50) -> List[Dict]:
        """
        Filter stock data based on bucket features with priority weighting
        
        Args:
            rfp_features: Features extracted from RFP line item
            stock_data: List of stock master entries
            max_results: Maximum number of results to return
            
        Returns:
            Filtered and scored list of stock entries
        """
        scored_items = []
        
        for stock_item in stock_data:
            # Combine all text fields for matching
            stock_text = ' '.join([
                str(stock_item.get('product_code', '')),
                str(stock_item.get('description', '')),
                str(stock_item.get('material', '')),
                str(stock_item.get('size', '')),
                str(stock_item.get('specification', ''))
            ])
            
            stock_features = self.extract_bucket_features(stock_text)
            score = self._calculate_match_score(rfp_features, stock_features)
            
            if score > 0:  # Only include items with some match
                scored_items.append({
                    **stock_item,
                    'match_score': score,
                    'matched_buckets': self._get_matched_buckets(rfp_features, stock_features)
                })
        
        # Sort by score (descending) and return top results
        scored_items.sort(key=lambda x: x['match_score'], reverse=True)
        return scored_items[:max_results]
    
    def _calculate_match_score(self, rfp_features: Dict[int, List[str]], 
                              stock_features: Dict[int, List[str]]) -> float:
        """Calculate match score based on bucket priorities and matches"""
        total_score = 0.0
        bucket_weights = {
            'high': 10.0,
            'medium': 5.0,
            'low': 2.0
        }
        
        for bucket_num in range(1, 12):
            if bucket_num in rfp_features and bucket_num in stock_features:
                bucket_priority = self.bucket_definitions[bucket_num]['priority']
                weight = bucket_weights[bucket_priority]
                
                # Calculate overlap between RFP and stock features for this bucket
                rfp_set = set(rfp_features[bucket_num])
                stock_set = set(stock_features[bucket_num])
                overlap = len(rfp_set.intersection(stock_set))
                
                if overlap > 0:
                    # Score based on overlap ratio and weight
                    overlap_ratio = overlap / max(len(rfp_set), len(stock_set))
                    total_score += weight * overlap_ratio
        
        return total_score
    
    def _get_matched_buckets(self, rfp_features: Dict[int, List[str]], 
                           stock_features: Dict[int, List[str]]) -> List[Dict]:
        """Get details of matched buckets for explanation"""
        matched_buckets = []
        
        for bucket_num in range(1, 12):
            if bucket_num in rfp_features and bucket_num in stock_features:
                rfp_set = set(rfp_features[bucket_num])
                stock_set = set(stock_features[bucket_num])
                overlap = rfp_set.intersection(stock_set)
                
                if overlap:
                    matched_buckets.append({
                        'bucket_number': bucket_num,
                        'bucket_name': self.bucket_definitions[bucket_num]['name'],
                        'priority': self.bucket_definitions[bucket_num]['priority'],
                        'matched_features': list(overlap),
                        'rfp_features': list(rfp_set),
                        'stock_features': list(stock_set)
                    })
        
        return matched_buckets
