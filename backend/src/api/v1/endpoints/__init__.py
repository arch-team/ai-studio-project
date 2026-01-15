"""API V1 Endpoints - REST route handlers.

Endpoint modules:
- training_jobs: Training job CRUD and lifecycle
- datasets: Dataset management
- models: ML model registry
- clusters: HyperPod cluster operations
- resource_limit_configs: Resource limit config admin API
- health: Health check endpoints
"""

from src.api.v1.endpoints.resource_limit_configs import (
    router as resource_limit_configs_router,
)

__all__ = ["resource_limit_configs_router"]
