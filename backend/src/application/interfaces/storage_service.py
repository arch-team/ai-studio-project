"""Storage Service Interface - S3/FSx storage operations contract.

Defines the port interface for object storage and file system operations.
Infrastructure layer provides concrete implementations for S3 and FSx.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
from datetime import datetime


class IStorageService(ABC):
    """Interface for storage operations.

    This interface abstracts storage backends (S3, FSx for Lustre),
    allowing the application layer to perform storage operations
    without depending on specific storage SDK implementations.
    """

    @abstractmethod
    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Upload a file to storage.

        Args:
            local_path: Local file path.
            remote_path: Destination path in storage.
            metadata: Optional metadata to attach.

        Returns:
            The remote path of the uploaded file.
        """
        pass

    @abstractmethod
    async def download_file(self, remote_path: str, local_path: str) -> str:
        """Download a file from storage.

        Args:
            remote_path: Source path in storage.
            local_path: Local destination path.

        Returns:
            The local path of the downloaded file.
        """
        pass

    @abstractmethod
    async def delete_file(self, remote_path: str) -> bool:
        """Delete a file from storage.

        Args:
            remote_path: Path of the file to delete.

        Returns:
            True if deleted successfully.
        """
        pass

    @abstractmethod
    async def list_files(
        self, prefix: str, max_results: int = 1000
    ) -> List[Dict[str, Any]]:
        """List files with a given prefix.

        Args:
            prefix: Path prefix to filter files.
            max_results: Maximum number of results.

        Returns:
            List of file metadata dictionaries.
        """
        pass

    @abstractmethod
    async def get_file_metadata(self, remote_path: str) -> Dict[str, Any]:
        """Get metadata for a file.

        Args:
            remote_path: Path of the file.

        Returns:
            File metadata including size, modified time, etc.
        """
        pass

    @abstractmethod
    async def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists.

        Args:
            remote_path: Path to check.

        Returns:
            True if the file exists.
        """
        pass

    @abstractmethod
    async def generate_presigned_url(
        self,
        remote_path: str,
        expiration: int = 3600,
        operation: str = "get",
    ) -> str:
        """Generate a presigned URL for direct access.

        Args:
            remote_path: Path of the file.
            expiration: URL expiration time in seconds.
            operation: 'get' for download, 'put' for upload.

        Returns:
            Presigned URL string.
        """
        pass

    @abstractmethod
    async def copy_file(self, source_path: str, dest_path: str) -> str:
        """Copy a file within storage.

        Args:
            source_path: Source file path.
            dest_path: Destination file path.

        Returns:
            The destination path.
        """
        pass

    @abstractmethod
    async def stream_file(
        self, remote_path: str, chunk_size: int = 8192
    ) -> AsyncIterator[bytes]:
        """Stream file contents.

        Args:
            remote_path: Path of the file.
            chunk_size: Size of each chunk in bytes.

        Yields:
            File content chunks.
        """
        pass
