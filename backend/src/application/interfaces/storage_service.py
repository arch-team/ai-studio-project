"""Storage Service Interface - S3/FSx storage operations contract."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class IStorageService(ABC):
    """Interface for storage operations (S3, FSx for Lustre)."""

    @abstractmethod
    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload a file to storage."""
        pass

    @abstractmethod
    async def download_file(self, remote_path: str, local_path: str) -> str:
        """Download a file from storage."""
        pass

    @abstractmethod
    async def delete_file(self, remote_path: str) -> bool:
        """Delete a file from storage."""
        pass

    @abstractmethod
    async def list_files(
        self, prefix: str, max_results: int = 1000
    ) -> list[dict[str, Any]]:
        """List files with a given prefix."""
        pass

    @abstractmethod
    async def get_file_metadata(self, remote_path: str) -> dict[str, Any]:
        """Get metadata for a file."""
        pass

    @abstractmethod
    async def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists."""
        pass

    @abstractmethod
    async def generate_presigned_url(
        self,
        remote_path: str,
        expiration: int = 3600,
        operation: str = "get",
    ) -> str:
        """Generate a presigned URL for direct access."""
        pass

    @abstractmethod
    async def copy_file(self, source_path: str, dest_path: str) -> str:
        """Copy a file within storage."""
        pass

    @abstractmethod
    async def stream_file(
        self, remote_path: str, chunk_size: int = 8192
    ) -> AsyncIterator[bytes]:
        """Stream file contents."""
        pass
