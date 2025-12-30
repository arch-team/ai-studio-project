"""模型管理REST API端点"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.model import (
    ModelCreate,
    ModelUpdate,
    ModelResponse,
    ModelListResponse,
    ModelVersionCreate,
    ModelVersionUpdate,
    ModelVersionResponse,
    ModelVersionListResponse,
    ModelFilesResponse,
    ModelFileInfo,
    ModelStorageStats,
)
from database import get_db
from models import User, ModelStatus, ModelFramework
from services.model.model_service import ModelService
from services.storage.model_storage import ModelStorageService
from config.settings import settings

router = APIRouter(prefix="/api/v1/models", tags=["models"])
logger = logging.getLogger(__name__)


# 依赖注入
async def get_current_user() -> User:
    """获取当前用户(临时实现)"""
    # TODO: 实现真实的用户认证
    return User(id=1, username="admin", email="admin@example.com")


def get_model_service() -> ModelService:
    """获取模型服务实例"""
    storage_service = ModelStorageService()
    return ModelService(storage_service)


# ==================== 模型管理端点 ====================


@router.post("/", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: ModelCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelResponse:
    """创建新模型

    Args:
        model_data: 模型创建数据
        db: 数据库会话
        current_user: 当前用户
        model_service: 模型服务

    Returns:
        ModelResponse: 创建的模型
    """
    try:
        model = await model_service.create_model(
            db=db,
            name=model_data.name,
            framework=model_data.framework,
            project_id=model_data.project_id,
            creator_id=current_user.id,
            description=model_data.description,
            task_type=model_data.task_type,
            source_training_job_id=model_data.source_training_job_id,
            tags=model_data.tags,
            metadata=model_data.metadata,
        )

        return ModelResponse.model_validate(model)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"创建模型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建模型失败"
        )


@router.get("/", response_model=ModelListResponse)
async def list_models(
    project_id: int | None = None,
    framework: ModelFramework | None = None,
    task_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelListResponse:
    """查询模型列表

    Args:
        project_id: 项目ID过滤
        framework: 框架过滤
        task_type: 任务类型过滤
        page: 页码
        page_size: 每页数量
        db: 数据库会话
        current_user: 当前用户
        model_service: 模型服务

    Returns:
        ModelListResponse: 模型列表响应
    """
    try:
        skip = (page - 1) * page_size
        models, total = await model_service.list_models(
            db=db,
            project_id=project_id,
            framework=framework,
            task_type=task_type,
            skip=skip,
            limit=page_size,
        )

        return ModelListResponse(
            items=[ModelResponse.model_validate(m) for m in models],
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"查询模型列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询模型列表失败"
        )


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelResponse:
    """获取模型详情

    Args:
        model_id: 模型ID
        db: 数据库会话
        current_user: 当前用户
        model_service: 模型服务

    Returns:
        ModelResponse: 模型详情
    """
    model = await model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型不存在: {model_id}"
        )

    return ModelResponse.model_validate(model)


@router.patch("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    model_data: ModelUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelResponse:
    """更新模型信息

    Args:
        model_id: 模型ID
        model_data: 更新数据
        db: 数据库会话
        current_user: 当前用户
        model_service: 模型服务

    Returns:
        ModelResponse: 更新后的模型
    """
    try:
        # 只更新提供的字段
        update_dict = model_data.model_dump(exclude_unset=True)
        model = await model_service.update_model(db, model_id, **update_dict)

        return ModelResponse.model_validate(model)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"更新模型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新模型失败"
        )


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: int,
    force: bool = False,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
):
    """删除模型

    Args:
        model_id: 模型ID
        force: 是否强制删除(硬删除文件)
        db: 数据库会话
        current_user: 当前用户
        model_service: 模型服务
    """
    try:
        await model_service.delete_model(db, model_id, force=force)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除模型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除模型失败"
        )


@router.get("/{model_id}/stats", response_model=ModelStorageStats)
async def get_model_stats(
    model_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelStorageStats:
    """获取模型存储统计

    Args:
        model_id: 模型ID
        current_user: 当前用户
        model_service: 模型服务

    Returns:
        ModelStorageStats: 存储统计
    """
    try:
        stats = await model_service.get_storage_stats(model_id)
        return ModelStorageStats(**stats)
    except Exception as e:
        logger.error(f"获取模型统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取模型统计失败"
        )


# ==================== 模型版本管理端点 ====================


@router.post("/{model_id}/versions", response_model=ModelVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_model_version_upload(
    model_id: int,
    version: str,
    file: UploadFile = File(...),
    description: str | None = None,
    model_format: str | None = None,
    model_architecture: str | None = None,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelVersionResponse:
    """上传文件创建模型版本

    Args:
        model_id: 模型ID
        version: 版本号
        file: 上传的文件
        description: 描述
        model_format: 模型格式
        model_architecture: 模型架构
        db: 数据库会话
        current_user: 当前用户
        model_service: 模型服务

    Returns:
        ModelVersionResponse: 创建的版本
    """
    try:
        model_version = await model_service.create_model_version(
            db=db,
            model_id=model_id,
            version=version,
            file_stream=file.file,
            filename=file.filename,
            description=description,
            model_format=model_format,
            model_architecture=model_architecture,
        )

        return ModelVersionResponse.model_validate(model_version)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"创建模型版本失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建模型版本失败"
        )


@router.get("/{model_id}/versions", response_model=ModelVersionListResponse)
async def list_model_versions(
    model_id: int,
    status_filter: ModelStatus | None = None,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelVersionListResponse:
    """查询模型的所有版本

    Args:
        model_id: 模型ID
        status_filter: 状态过滤
        db: 数据库会话
        current_user: 当前用户
        model_service: 模型服务

    Returns:
        ModelVersionListResponse: 版本列表
    """
    try:
        versions = await model_service.list_model_versions(
            db=db,
            model_id=model_id,
            status=status_filter,
        )

        return ModelVersionListResponse(
            items=[ModelVersionResponse.model_validate(v) for v in versions]
        )

    except Exception as e:
        logger.error(f"查询模型版本列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询模型版本列表失败"
        )


@router.get("/{model_id}/versions/{version_id}", response_model=ModelVersionResponse)
async def get_model_version(
    model_id: int,
    version_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelVersionResponse:
    """获取模型版本详情

    Args:
        model_id: 模型ID
        version_id: 版本ID
        db: 数据库会话
        current_user: 当前用户
        model_service: 模型服务

    Returns:
        ModelVersionResponse: 版本详情
    """
    version = await model_service.get_model_version(db, version_id)
    if not version or version.model_id != model_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"版本不存在: {version_id}"
        )

    return ModelVersionResponse.model_validate(version)


@router.patch("/{model_id}/versions/{version_id}", response_model=ModelVersionResponse)
async def update_model_version(
    model_id: int,
    version_id: int,
    version_data: ModelVersionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelVersionResponse:
    """更新模型版本信息

    Args:
        model_id: 模型ID
        version_id: 版本ID
        version_data: 更新数据
        db: 数据库会话
        current_user: 当前用户
        model_service: 模型服务

    Returns:
        ModelVersionResponse: 更新后的版本
    """
    try:
        # 验证版本属于该模型
        version = await model_service.get_model_version(db, version_id)
        if not version or version.model_id != model_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"版本不存在: {version_id}"
            )

        # 只更新提供的字段
        update_dict = version_data.model_dump(exclude_unset=True)
        version = await model_service.update_model_version(db, version_id, **update_dict)

        return ModelVersionResponse.model_validate(version)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"更新模型版本失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新模型版本失败"
        )


@router.post("/{model_id}/versions/{version_id}/publish", response_model=ModelVersionResponse)
async def publish_model_version(
    model_id: int,
    version_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelVersionResponse:
    """发布模型版本

    Args:
        model_id: 模型ID
        version_id: 版本ID
        db: 数据库会话
        current_user: 当前用户
        model_service: 模型服务

    Returns:
        ModelVersionResponse: 发布后的版本
    """
    try:
        # 验证版本属于该模型
        version = await model_service.get_model_version(db, version_id)
        if not version or version.model_id != model_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"版本不存在: {version_id}"
            )

        version = await model_service.publish_model_version(
            db=db,
            version_id=version_id,
            publisher_id=current_user.id,
        )

        return ModelVersionResponse.model_validate(version)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"发布模型版本失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发布模型版本失败"
        )


@router.delete("/{model_id}/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_version(
    model_id: int,
    version_id: int,
    force: bool = False,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
):
    """删除模型版本

    Args:
        model_id: 模型ID
        version_id: 版本ID
        force: 是否强制删除(硬删除文件)
        db: 数据库会话
        current_user: 当前用户
        model_service: 模型服务
    """
    try:
        # 验证版本属于该模型
        version = await model_service.get_model_version(db, version_id)
        if not version or version.model_id != model_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"版本不存在: {version_id}"
            )

        await model_service.delete_model_version(db, version_id, force=force)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除模型版本失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除模型版本失败"
        )


@router.get("/{model_id}/versions/{version}/files", response_model=ModelFilesResponse)
async def list_model_files(
    model_id: int,
    version: str,
    current_user: Annotated[User, Depends(get_current_user)],
    model_service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelFilesResponse:
    """获取模型版本的文件列表

    Args:
        model_id: 模型ID
        version: 版本号
        current_user: 当前用户
        model_service: 模型服务

    Returns:
        ModelFilesResponse: 文件列表
    """
    try:
        files = await model_service.get_model_files(model_id, version)
        return ModelFilesResponse(
            files=[ModelFileInfo(**f) for f in files]
        )
    except Exception as e:
        logger.error(f"获取模型文件列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取模型文件列表失败"
        )


__all__ = ["router"]
