import os
import json
import logging
from typing import Dict, Optional
from flask import session
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SessionService:
    """Service for managing user sessions and data isolation"""
    
    def __init__(self):
        self.session_timeout_hours = 24  # Session expires after 24 hours
    
    def get_or_create_session_id(self) -> str:
        """Get existing session ID or create a new one"""
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            session['created_at'] = datetime.now().isoformat()
            session.permanent = True
            logger.info(f"Created new session: {session['session_id']}")
        
        return session['session_id']
    
    def get_session_id(self) -> Optional[str]:
        """Get current session ID if exists"""
        return session.get('session_id')
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid and not expired"""
        if 'session_id' not in session or 'created_at' not in session:
            return False
        
        try:
            created_at = datetime.fromisoformat(session['created_at'])
            expiry_time = created_at + timedelta(hours=self.session_timeout_hours)
            return datetime.now() < expiry_time
        except Exception as e:
            logger.error(f"Error checking session validity: {e}")
            return False
    
    def refresh_session(self):
        """Refresh session timestamp"""
        if 'session_id' in session:
            session['last_activity'] = datetime.now().isoformat()
    
    def clear_session(self):
        """Clear current session"""
        session_id = session.get('session_id')
        session.clear()
        logger.info(f"Cleared session: {session_id}")
    
    def get_session_info(self) -> Dict:
        """Get session information"""
        if not self.is_session_valid():
            return {'valid': False}
        
        return {
            'valid': True,
            'session_id': session.get('session_id'),
            'created_at': session.get('created_at'),
            'last_activity': session.get('last_activity'),
            'expires_in_hours': self.session_timeout_hours
        }
    
    def set_session_data(self, key: str, value: any):
        """Set session-specific data"""
        session[key] = value
    
    def get_session_data(self, key: str, default=None):
        """Get session-specific data"""
        return session.get(key, default)
    
    def has_stock_master(self) -> bool:
        """Check if user has uploaded stock master in this session"""
        return session.get('stock_master_uploaded', False)
    
    def set_stock_master_uploaded(self, blob_name: str, record_count: int):
        """Mark stock master as uploaded for this session"""
        session['stock_master_uploaded'] = True
        session['stock_master_blob'] = blob_name
        session['stock_master_records'] = record_count
        session['stock_master_uploaded_at'] = datetime.now().isoformat()
    
    def get_stock_master_info(self) -> Optional[Dict]:
        """Get stock master information for current session"""
        if not self.has_stock_master():
            return None
        
        return {
            'blob_name': session.get('stock_master_blob'),
            'record_count': session.get('stock_master_records'),
            'uploaded_at': session.get('stock_master_uploaded_at')
        }
    
    def clear_stock_master(self):
        """Clear stock master data from session"""
        session.pop('stock_master_uploaded', None)
        session.pop('stock_master_blob', None)
        session.pop('stock_master_records', None)
        session.pop('stock_master_uploaded_at', None)
