"""Space API dependencies - 依赖注入函数."""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.quotas.infrastructure import QuotaCheckerImpl, ResourceQuotaRepository
from src.modules.spaces.application.interfaces import ISpaceBackendClient
from src.modules.spaces.application.services import SpaceService
from src.modules.spaces.application.services.sagemaker_metrics_service import SpaceMetricsService
from src.modules.spaces.domain.value_objects import SpaceBackend
from src.modules.spaces.infrastructure.external import (
    HyperPodSpaceBackend,
    K8sWorkspaceClient,
    StudioSpaceBackend,
    get_sagemaker_spaces_client,
)
from src.modules.spaces.infrastructure.repositories import SpaceRepository
from src.shared.domain.interfaces import IQuotaChecker
from src.shared.infrastructure.database import get_db


@lru_cache(maxsize=1)
def get_studio_backend() -> ISpaceBackendClient:
    """获取 Studio SpaceBackend 单例。"""
    sagemaker_client = get_sagemaker_spaces_client()
    return StudioSpaceBackend(sagemaker_client)


@lru_cache(maxsize=1)
def get_hyperpod_backend() -> ISpaceBackendClient:
    """获取 HyperPod SpaceBackend 单例。"""
    k8s_client = K8sWorkspaceClient()
    return HyperPodSpaceBackend(k8s_client)


def get_space_metrics_service() -> SpaceMetricsService:
    """获取 SpaceMetricsService 单例."""
    return SpaceMetricsService()


async def get_quota_checker(
    session: AsyncSession = Depends(get_db),
) -> IQuotaChecker:
    """依赖注入：配额检查器（跨模块组装，参照 training 模块）。"""
    quota_repository = ResourceQuotaRepository(session)
    return QuotaCheckerImpl(quota_repository)


async def get_space_service(
    session: AsyncSession = Depends(get_db),
    quota_checker: IQuotaChecker = Depends(get_quota_checker),
    metrics_service: SpaceMetricsService = Depends(get_space_metrics_service),
) -> SpaceService:
    """获取 SpaceService 实例 - 新签名：双后端 + quota_checker + metrics_service。"""
    space_repository = SpaceRepository(session)
    backends: dict[SpaceBackend, ISpaceBackendClient] = {
        SpaceBackend.STUDIO: get_studio_backend(),
        SpaceBackend.HYPERPOD: get_hyperpod_backend(),
    }
    return SpaceService(
        space_repository=space_repository,
        backends=backends,
        quota_checker=quota_checker,
        metrics_service=metrics_service,
    )
