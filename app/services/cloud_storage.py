"""Cloud Storage service for document management.

This module provides Google Cloud Storage integration for document upload,
download, and management with signed URLs and lifecycle policies.
"""

import os
import mimetypes
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
import uuid

from google.cloud import storage
from google.cloud.storage import Blob, Bucket
from google.cloud.exceptions import NotFound, GoogleCloudError

from app.core.config import settings
from app.core.firebase import get_storage
from app.core.logging import logger


class CloudStorageService:
    """Google Cloud Storage service for document management."""
    
    def __init__(self):
        """Initialize Cloud Storage service."""
        self.bucket = get_storage()
        self.bucket_name = settings.FIREBASE_STORAGE_BUCKET
        
        # Document storage paths
        self.documents_path = "documents"
        self.temp_path = "temp"
        self.processed_path = "processed"
        
        # Allowed file types
        self.allowed_extensions = {
            '.pdf', '.doc', '.docx', '.txt', '.md', 
            '.png', '.jpg', '.jpeg', '.gif', '.webp'
        }
        
        # Max file size (50MB)
        self.max_file_size = 50 * 1024 * 1024
    
    async def upload_document(
        self,
        file_data: bytes,
        filename: str,
        user_id: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Upload document to Cloud Storage.
        
        Args:
            file_data: File content as bytes
            filename: Original filename
            user_id: User ID who uploaded the file
            content_type: MIME type of the file
            metadata: Additional metadata
            
        Returns:
            Dict[str, Any]: Upload result with file info
            
        Raises:
            ValueError: If file validation fails
            GoogleCloudError: If upload fails
        """
        try:
            # Validate file
            self._validate_file(file_data, filename)
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_ext = Path(filename).suffix.lower()
            storage_filename = f"{file_id}{file_ext}"
            
            # Create storage path
            storage_path = f"{self.documents_path}/{user_id}/{storage_filename}"
            
            # Detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Create blob
            blob = self.bucket.blob(storage_path)
            
            # Set metadata
            blob_metadata = {
                'original_filename': filename,
                'user_id': user_id,
                'file_id': file_id,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'content_type': content_type
            }
            
            if metadata:
                blob_metadata.update(metadata)
            
            blob.metadata = blob_metadata
            blob.content_type = content_type
            
            # Upload file
            blob.upload_from_string(file_data, content_type=content_type)
            
            logger.info(f"Document uploaded successfully: {storage_path}")
            
            return {
                'file_id': file_id,
                'storage_path': storage_path,
                'original_filename': filename,
                'size': len(file_data),
                'content_type': content_type,
                'public_url': blob.public_url,
                'gs_url': f"gs://{self.bucket_name}/{storage_path}",
                'metadata': blob_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to upload document: {e}")
            raise GoogleCloudError(f"Upload failed: {str(e)}")
    
    async def download_document(self, storage_path: str) -> bytes:
        """Download document from Cloud Storage.
        
        Args:
            storage_path: Path to file in storage
            
        Returns:
            bytes: File content
            
        Raises:
            NotFound: If file doesn't exist
            GoogleCloudError: If download fails
        """
        try:
            blob = self.bucket.blob(storage_path)
            
            if not blob.exists():
                raise NotFound(f"File not found: {storage_path}")
            
            content = blob.download_as_bytes()
            logger.info(f"Document downloaded: {storage_path}")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to download document: {e}")
            raise
    
    async def get_signed_url(
        self,
        storage_path: str,
        expiration: int = 3600,
        method: str = 'GET'
    ) -> str:
        """Generate signed URL for document access.
        
        Args:
            storage_path: Path to file in storage
            expiration: URL expiration time in seconds
            method: HTTP method ('GET', 'PUT', 'POST', 'DELETE')
            
        Returns:
            str: Signed URL
            
        Raises:
            NotFound: If file doesn't exist
        """
        try:
            blob = self.bucket.blob(storage_path)
            
            # For GET requests, check if file exists
            if method == 'GET' and not blob.exists():
                raise NotFound(f"File not found: {storage_path}")
            
            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.utcnow() + timedelta(seconds=expiration),
                method=method,
            )
            
            logger.info(f"Generated signed URL for: {storage_path}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise
    
    async def delete_document(self, storage_path: str) -> bool:
        """Delete document from Cloud Storage.
        
        Args:
            storage_path: Path to file in storage
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            blob = self.bucket.blob(storage_path)
            
            if blob.exists():
                blob.delete()
                logger.info(f"Document deleted: {storage_path}")
                return True
            else:
                logger.warning(f"Document not found for deletion: {storage_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    async def list_user_documents(
        self,
        user_id: str,
        prefix: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List documents for a user.
        
        Args:
            user_id: User ID
            prefix: Optional prefix filter
            limit: Maximum number of files to return
            
        Returns:
            List[Dict[str, Any]]: List of document info
        """
        try:
            folder_prefix = f"{self.documents_path}/{user_id}/"
            if prefix:
                folder_prefix += prefix
            
            blobs = self.bucket.list_blobs(prefix=folder_prefix, max_results=limit)
            
            documents = []
            for blob in blobs:
                doc_info = {
                    'name': blob.name,
                    'size': blob.size,
                    'created': blob.time_created.isoformat() if blob.time_created else None,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'content_type': blob.content_type,
                    'metadata': blob.metadata or {},
                    'public_url': blob.public_url,
                    'gs_url': f"gs://{self.bucket_name}/{blob.name}"
                }
                documents.append(doc_info)
            
            logger.info(f"Listed {len(documents)} documents for user: {user_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []
    
    async def get_document_info(self, storage_path: str) -> Optional[Dict[str, Any]]:
        """Get document information.
        
        Args:
            storage_path: Path to file in storage
            
        Returns:
            Optional[Dict[str, Any]]: Document info or None if not found
        """
        try:
            blob = self.bucket.blob(storage_path)
            
            if not blob.exists():
                return None
            
            # Reload to get latest metadata
            blob.reload()
            
            return {
                'name': blob.name,
                'size': blob.size,
                'created': blob.time_created.isoformat() if blob.time_created else None,
                'updated': blob.updated.isoformat() if blob.updated else None,
                'content_type': blob.content_type,
                'metadata': blob.metadata or {},
                'public_url': blob.public_url,
                'gs_url': f"gs://{self.bucket_name}/{blob.name}"
            }
            
        except Exception as e:
            logger.error(f"Failed to get document info: {e}")
            return None
    
    async def move_document(self, source_path: str, destination_path: str) -> bool:
        """Move document to different location.
        
        Args:
            source_path: Current path
            destination_path: New path
            
        Returns:
            bool: True if moved successfully
        """
        try:
            source_blob = self.bucket.blob(source_path)
            
            if not source_blob.exists():
                logger.warning(f"Source file not found: {source_path}")
                return False
            
            # Copy to new location
            destination_blob = self.bucket.copy_blob(source_blob, self.bucket, destination_path)
            
            # Delete original
            source_blob.delete()
            
            logger.info(f"Document moved: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move document: {e}")
            return False
    
    async def update_metadata(
        self,
        storage_path: str,
        metadata: Dict[str, str]
    ) -> bool:
        """Update document metadata.
        
        Args:
            storage_path: Path to file in storage
            metadata: New metadata
            
        Returns:
            bool: True if updated successfully
        """
        try:
            blob = self.bucket.blob(storage_path)
            
            if not blob.exists():
                raise NotFound(f"File not found: {storage_path}")
            
            # Get current metadata
            blob.reload()
            current_metadata = blob.metadata or {}
            
            # Merge with new metadata
            current_metadata.update(metadata)
            current_metadata['last_modified'] = datetime.utcnow().isoformat()
            
            # Update
            blob.metadata = current_metadata
            blob.patch()
            
            logger.info(f"Metadata updated for: {storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            return False
    
    def _validate_file(self, file_data: bytes, filename: str) -> None:
        """Validate uploaded file.
        
        Args:
            file_data: File content
            filename: Original filename
            
        Raises:
            ValueError: If validation fails
        """
        # Check file size
        if len(file_data) > self.max_file_size:
            raise ValueError(f"File too large: {len(file_data)} bytes (max: {self.max_file_size})")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise ValueError(f"File type not allowed: {file_ext}")
        
        # Check if file is empty
        if len(file_data) == 0:
            raise ValueError("File is empty")
        
        logger.info(f"File validation passed: {filename} ({len(file_data)} bytes)")


# Global instance
cloud_storage_service = CloudStorageService()