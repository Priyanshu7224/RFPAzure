import os
import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class AzureOpenAIService:
    """Service for Azure OpenAI integration"""

    def __init__(self):
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2023-12-01-preview')
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')

        # For demo purposes, we'll use a mock client if Azure OpenAI is not configured
        self.client = None
        self.use_mock = not (self.api_key and self.endpoint)

        if not self.use_mock:
            try:
                from openai import AzureOpenAI
                logger.info(f"Initializing Azure OpenAI client with endpoint: {self.endpoint}")
                logger.info(f"Using deployment: {self.deployment_name}, API version: {self.api_version}")

                self.client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint
                )
                logger.info("Azure OpenAI client initialized successfully")

                # Test the client with a simple call
                test_response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                logger.info("Azure OpenAI client test successful")

            except ImportError as e:
                logger.error(f"Failed to import openai package: {e}. Using mock responses.")
                self.use_mock = True
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {e}. Using mock responses.")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Error details: {str(e)}")
                self.use_mock = True
    
    def test_connection(self) -> bool:
        """Test Azure OpenAI connection"""
        if self.use_mock:
            return True

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"Azure OpenAI connection test failed: {str(e)}")
            return False
    
    def match_rfp_item(self, rfp_line: str, stock_entries: List[Dict]) -> Dict[str, Any]:
        """
        Use Azure OpenAI to match RFP line item with stock entries

        Args:
            rfp_line: The RFP line item description
            stock_entries: List of filtered stock entries to match against

        Returns:
            Dict containing match results
        """
        if self.use_mock:
            return self._mock_match_rfp_item(rfp_line, stock_entries)

        try:
            # Prepare the prompt with bucket-based matching strategy
            prompt = self._build_matching_prompt(rfp_line, stock_entries)

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a highly knowledgeable industrial procurement assistant trained to interpret messy or semi-structured RFP line items. Your job is to find the most relevant product from the given stock master entries using the bucket-based search strategy."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Validate the response format
            required_fields = ['matched_product_code', 'matched_description', 'match_score', 'match_reason']
            if not all(field in result for field in required_fields):
                raise ValueError("Invalid response format from Azure OpenAI")

            return result

        except Exception as e:
            logger.error(f"Error in Azure OpenAI matching: {str(e)}")
            return {
                "matched_product_code": "",
                "matched_description": "",
                "match_score": "0",
                "on_hand_quantity": 0,
                "match_reason": f"Error in AI matching: {str(e)}"
            }
    
    def _build_matching_prompt(self, rfp_line: str, stock_entries: List[Dict]) -> str:
        """Build the matching prompt with bucket strategy"""
        
        bucket_strategy = """
Use the following search strategy, based on bucket logic:

Bucket 1 - Class Rating (Priority: High): 150, 150#, 300, 300#, 600, 600#, 900, 900#, 1500, 1500#, 2500, 2500#, 5000, 5000#, 3000, 3000#, 6000, 6000#, 9000, 9000#
Bucket 2 - Item Group (Priority: High): Pipe, Elbow, Cap, Flange, Flg, Tee, Reducer, Redg, Red, Bend, Swage, Coupling, Clpg, Boss, Union, Nipple, Plug, Cross, Insert, Pipet, Weldolet, Sockolet, Elbolet, Threadolet
Bucket 3 - Flange Type/Facing (Priority: High): RF, Raised face, FF, Flat face, WN, WNRF, WN RF, WNFF, WN FF, Weldneck, Weld Neck, Blind, BL, BLRF, BL RF, BLFF, BF FF, SO, SORF, SO RF, SOFF, SO FF, Slip On, Slipon, Slip-On, LJ, LJRF, LJ RF, LJFF, LJ FF, Lap Joint, Lapjoint, Lap-Joint
Bucket 4 - Item Ends/Finish (Priority: High): NPT, threaded, TH, Scrd, Screwed, SW, Socket weld, Socketweld, BW, Buttweld, Smls, Seamless, Welded, WE
Bucket 5 - Elbow Type (Priority: High): LR, Long Radius, SR, Short Radius, 90LR, 90SR, 90, 90Deg, 90D, 90 Deg, 90 Degree, 45LR, 45SR, 45, 45Deg, 45D, 45 Deg, 45 Degree, 180LR, 180SR, 180, 180Deg, 180D, 180 Deg, 180 Degree
Bucket 6 - Item Type (Priority: High): Eq, Equal, Ecc, Eccentric, Con, Conc, Concentric, Red, Reducing, Redg, Full, Half, Hex, Bull, Round
Bucket 7 - Material (Priority: Medium): CS, Carbon Steel, Carbonsteel, SS, Stainless Steel, Stainlesssteel, X52, X42, A53, SA/A106-B, A106-B, A106B, A106GRB, A106 GRB, SA/A333 GR.6, A333GR6, A333 GR6, 304, SS304, SS304/L, SS304L, 316, SS316, SS316/L, SS316L, TP304/L, TP304, TP304L, TP316, TP316/L, TP316L, SA/A234 WPB, 234WPB, A234WPB, A234, 234, SA/A105N, A105, A105N, 105, F304/304L, 304/304L, F304/L, F304L, 304L, F316/316L, 316/316L, F316/L, F316L, 316L, 304/L, 316/L, WP304/L, WP304/304L, F304/L, F304L, WP316/L, WP316/316L, F316/L, F316L
Bucket 8 - Thickness (Priority: Medium): S10, S20, S30, S40, S60, S80, S100, S120, S140, S160, SSTD, SXS, SXXS, SCH 10, SCH 20, SCH 30, SCH 40, SCH 60, SCH 80, SCH 100, SCH 120, SCH 140, SCH 160, SCH STD, SCH XS, SCH XXS SCH10, SCH20, SCH30, SCH40, SCH60, SCH80, SCH100, SCH120, SCH140, SCH160, SCHSTD, SCHXS, SCHXXS, STD, XS, XXS
Bucket 9 - Size 1 (Priority: Low): 1/8", 1/4", 1/2", 3/4", 1", 1.1/4", 1.1/2", 2", 2.1/2", 3", 3.1/2", 4", 5", 6", 7", 8", 10", 12", 14", 16", 18", 20", 22", 24", 26", 28", 30", 32", 34", 36", 38", 40", 42", 44"
Bucket 10 - Size 2 (Priority: Low): Same as Size 1
Bucket 11 - Misc (Priority: Low): API, PSL1, PSL2, PSL3, TYPE A, TYPE B, TYPE C

Prioritize matches based on Buckets 1-6 (High Priority). Use Buckets 7-11 for additional context but be flexible with deviations.

Handle common format variations:
- 'NB 6.0 7.11MM SMLS PIPE' → '6" SCH40 SMLS PIPE'
- 'DN100 STD a234 90 degree long radius' → '4" SCH40 90LR ELBOW A234 WPB'
"""
        
        stock_entries_json = json.dumps(stock_entries, indent=2)
        
        prompt = f"""{bucket_strategy}

### RFP Line Item:
"{rfp_line}"

### Stock Master Entries (JSON List):
{stock_entries_json}

### Desired Output Format (JSON):
{{
  "matched_product_code": "...",
  "matched_description": "...",
  "match_score": "...",
  "on_hand_quantity": ...,
  "match_reason": "..."
}}

Provide a match score from 0-100 based on how well the RFP item matches the stock entry. Include detailed reasoning explaining which buckets were matched and any format conversions applied."""
        
        return prompt

    def _mock_match_rfp_item(self, rfp_line: str, stock_entries: List[Dict]) -> Dict[str, Any]:
        """
        Mock matching function for demo purposes when Azure OpenAI is not available
        """
        if not stock_entries:
            return {
                "matched_product_code": "",
                "matched_description": "",
                "match_score": "0",
                "on_hand_quantity": 0,
                "match_reason": "No stock entries provided for matching"
            }

        # Simple keyword-based matching for demo
        rfp_lower = rfp_line.lower()
        best_match = None
        best_score = 0

        for entry in stock_entries:
            score = 0
            description = entry.get('description', '').lower()
            product_code = entry.get('product_code', '').lower()

            # Simple scoring based on keyword matches
            keywords = ['pipe', 'flange', 'elbow', 'tee', 'reducer', 'cap', 'valve', 'bolt', 'nut', 'gasket']
            for keyword in keywords:
                if keyword in rfp_lower and keyword in description:
                    score += 20

            # Size matching
            import re
            rfp_sizes = re.findall(r'\d+"|\d+\.\d+"|\d+mm|\d+\.?\d*mm', rfp_lower)
            desc_sizes = re.findall(r'\d+"|\d+\.\d+"|\d+mm|\d+\.?\d*mm', description)

            for rfp_size in rfp_sizes:
                if rfp_size in desc_sizes:
                    score += 30

            # Material matching
            materials = ['a105', 'a234', 'ss316', 'ss304', 'x52', 'wpb']
            for material in materials:
                if material in rfp_lower and material in description:
                    score += 25

            if score > best_score:
                best_score = score
                best_match = entry

        if best_match and best_score > 40:
            return {
                "matched_product_code": best_match.get('product_code', ''),
                "matched_description": best_match.get('description', ''),
                "match_score": str(min(best_score, 95)),
                "on_hand_quantity": int(best_match.get('on_hand_quantity', 0) or 0),
                "match_reason": f"Mock AI matching based on keyword analysis. Score: {best_score}"
            }
        else:
            return {
                "matched_product_code": "",
                "matched_description": "",
                "match_score": "0",
                "on_hand_quantity": 0,
                "match_reason": "No suitable match found using mock AI matching"
            }
