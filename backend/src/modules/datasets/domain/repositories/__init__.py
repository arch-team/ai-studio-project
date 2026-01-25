"""Dataset 仓库接口。"""

from .dataset_repository import IDatasetRepository
from .upload_session_repository import IUploadSessionRepository

__all__ = ["IDatasetRepository", "IUploadSessionRepository"]
