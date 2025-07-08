import os
import json
import logging
from typing import Dict, List, Optional, BinaryIO
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import ResourceNotFoundError
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class AzureStorageService:
    """Service for Azure Blob Storage operations"""
    
    def __init__(self):
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.container_name = os.getenv('AZURE_CONTAINER_NAME', 'rfp-bom-data')
        self.use_azure = bool(self.connection_string)
        
        if self.use_azure:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
                self._ensure_container_exists()
                logger.info("Azure Blob Storage initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Azure Blob Storage: {e}. Using local storage.")
                self.use_azure = False
        else:
            logger.info("Azure Blob Storage not configured. Using local storage.")
    
    def _ensure_container_exists(self):
        """Ensure the container exists"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            container_client.get_container_properties()
        except ResourceNotFoundError:
            container_client = self.blob_service_client.create_container(self.container_name)
            logger.info(f"Created container: {self.container_name}")
    
    def generate_user_session_id(self) -> str:
        """Generate a unique session ID for user data isolation"""
        return str(uuid.uuid4())
    
    def upload_file(self, file_content: bytes, filename: str, session_id: str, file_type: str = 'stock') -> str:
        """
        Upload file to Azure Blob Storage or local storage
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            session_id: User session ID for data isolation
            file_type: Type of file ('stock', 'rfp', 'export')
            
        Returns:
            Blob name or local file path
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        blob_name = f"{session_id}/{file_type}/{timestamp}_{filename}"
        
        if self.use_azure:
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name, 
                    blob=blob_name
                )
                blob_client.upload_blob(file_content, overwrite=True)
                logger.info(f"Uploaded file to Azure Blob: {blob_name}")
                return blob_name
            except Exception as e:
                logger.error(f"Failed to upload to Azure Blob: {e}")
                # Fallback to local storage
                return self._save_local_file(file_content, blob_name)
        else:
            return self._save_local_file(file_content, blob_name)
    
    def download_file(self, blob_name: str) -> Optional[bytes]:
        """Download file from Azure Blob Storage or local storage"""
        if self.use_azure:
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name, 
                    blob=blob_name
                )
                return blob_client.download_blob().readall()
            except Exception as e:
                logger.error(f"Failed to download from Azure Blob: {e}")
                return self._load_local_file(blob_name)
        else:
            return self._load_local_file(blob_name)
    
    def save_json_data(self, data: Dict, session_id: str, data_type: str = 'stock_master') -> str:
        """Save JSON data to storage"""
        json_content = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
        filename = f"{data_type}.json"
        return self.upload_file(json_content, filename, session_id, 'data')
    
    def load_json_data(self, blob_name: str) -> Optional[Dict]:
        """Load JSON data from storage"""
        try:
            content = self.download_file(blob_name)
            if content:
                return json.loads(content.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to load JSON data: {e}")
        return None
    
    def list_user_files(self, session_id: str, file_type: str = None) -> List[Dict]:
        """List files for a specific user session"""
        if self.use_azure:
            try:
                container_client = self.blob_service_client.get_container_client(self.container_name)
                prefix = f"{session_id}/"
                if file_type:
                    prefix += f"{file_type}/"
                
                blobs = []
                for blob in container_client.list_blobs(name_starts_with=prefix):
                    blobs.append({
                        'name': blob.name,
                        'size': blob.size,
                        'last_modified': blob.last_modified,
                        'url': f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{self.container_name}/{blob.name}"
                    })
                return blobs
            except Exception as e:
                logger.error(f"Failed to list Azure blobs: {e}")
                return []
        else:
            return self._list_local_files(session_id, file_type)
    
    def delete_file(self, blob_name: str) -> bool:
        """Delete file from storage"""
        if self.use_azure:
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name, 
                    blob=blob_name
                )
                blob_client.delete_blob()
                logger.info(f"Deleted Azure blob: {blob_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete Azure blob: {e}")
                return self._delete_local_file(blob_name)
        else:
            return self._delete_local_file(blob_name)
    
    def _save_local_file(self, content: bytes, filepath: str) -> str:
        """Save file locally as fallback"""
        local_path = os.path.join('uploads', filepath)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Saved file locally: {local_path}")
        return filepath
    
    def _load_local_file(self, filepath: str) -> Optional[bytes]:
        """Load file from local storage"""
        local_path = os.path.join('uploads', filepath)
        try:
            with open(local_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Local file not found: {local_path}")
            return None
    
    def _list_local_files(self, session_id: str, file_type: str = None) -> List[Dict]:
        """List local files for session"""
        base_path = os.path.join('uploads', session_id)
        if file_type:
            base_path = os.path.join(base_path, file_type)
        
        files = []
        if os.path.exists(base_path):
            for root, dirs, filenames in os.walk(base_path):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    relative_path = os.path.relpath(filepath, 'uploads')
                    stat = os.stat(filepath)
                    files.append({
                        'name': relative_path.replace('\\', '/'),
                        'size': stat.st_size,
                        'last_modified': datetime.fromtimestamp(stat.st_mtime),
                        'url': f'/download/{relative_path.replace(os.sep, "/")}'
                    })
        return files
    
    def _delete_local_file(self, filepath: str) -> bool:
        """Delete local file"""
        local_path = os.path.join('uploads', filepath)
        try:
            os.remove(local_path)
            logger.info(f"Deleted local file: {local_path}")
            return True
        except FileNotFoundError:
            logger.error(f"Local file not found: {local_path}")
            return False
    
    def get_storage_info(self) -> Dict:
        """Get storage configuration information"""
        return {
            'storage_type': 'Azure Blob Storage' if self.use_azure else 'Local Storage',
            'container_name': self.container_name if self.use_azure else 'uploads/',
            'configured': self.use_azure,
            'connection_available': bool(self.connection_string)
        }
