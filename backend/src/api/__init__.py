"""API包"""

from .rest.training import router as training_router
from .rest.model import router as model_router

__all__ = ["training_router", "model_router"]
