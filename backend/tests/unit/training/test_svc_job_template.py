"""JobTemplateService 单元测试。

覆盖所有 CRUD 操作、权限检查、重复名称校验等核心业务逻辑。
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.modules.training.application.services.job_template_service import JobTemplateService
from src.modules.training.domain.entities import JobTemplate
from src.modules.training.domain.exceptions import (
    JobTemplateNotFoundError,
    JobTemplatePermissionDeniedError,
)
from src.modules.training.domain.value_objects import TemplateVisibility
from src.shared.domain.exceptions import DuplicateEntityError


@pytest.fixture
def mock_template_repository() -> AsyncMock:
    """创建 Mock IJobTemplateRepository。"""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.soft_delete = AsyncMock()
    repo.exists_by_name_and_owner = AsyncMock(return_value=False)
    repo.list_visible_templates = AsyncMock(return_value=([], 0))
    repo.get_popular_templates = AsyncMock(return_value=[])
    repo.increment_usage_count = AsyncMock()
    return repo


@pytest.fixture
def sample_template() -> JobTemplate:
    """创建测试用 JobTemplate 实体。"""
    return JobTemplate(
        id=1,
        name="test-template",
        owner_id=10,
        training_config={"framework": "pytorch", "gpu_count": 4},
        description="测试模板",
        visibility=TemplateVisibility.PRIVATE,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def public_template() -> JobTemplate:
    """创建公开可见的 JobTemplate 实体。"""
    return JobTemplate(
        id=2,
        name="public-template",
        owner_id=10,
        training_config={"framework": "pytorch", "gpu_count": 8},
        description="公开模板",
        visibility=TemplateVisibility.PUBLIC,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def service(mock_template_repository: AsyncMock) -> JobTemplateService:
    """创建 JobTemplateService 实例。"""
    return JobTemplateService(repository=mock_template_repository)


# ==================== create_template ====================


class TestCreateTemplate:
    """测试创建模板。"""

    async def test_create_template_success(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
    ) -> None:
        """成功创建模板。"""
        created_template = JobTemplate(
            id=1,
            name="new-template",
            owner_id=10,
            training_config={"framework": "pytorch"},
        )
        mock_template_repository.create.return_value = created_template

        result = await service.create_template(
            owner_id=10,
            data={
                "name": "new-template",
                "training_config": {"framework": "pytorch"},
            },
        )

        assert result.id == 1
        assert result.name == "new-template"
        mock_template_repository.exists_by_name_and_owner.assert_called_once_with("new-template", 10)
        mock_template_repository.create.assert_called_once()

    async def test_create_template_with_visibility(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
    ) -> None:
        """创建带 visibility 的模板。"""
        created_template = JobTemplate(
            id=1,
            name="public-template",
            owner_id=10,
            training_config={"framework": "pytorch"},
            visibility=TemplateVisibility.PUBLIC,
        )
        mock_template_repository.create.return_value = created_template

        result = await service.create_template(
            owner_id=10,
            data={
                "name": "public-template",
                "training_config": {"framework": "pytorch"},
                "visibility": "PUBLIC",
            },
        )

        assert result.name == "public-template"
        mock_template_repository.create.assert_called_once()

    async def test_create_template_default_visibility_private(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
    ) -> None:
        """创建模板时默认 visibility 为 PRIVATE。"""
        mock_template_repository.create.return_value = JobTemplate(
            id=1,
            name="test",
            owner_id=10,
            training_config={"framework": "pytorch"},
        )

        await service.create_template(
            owner_id=10,
            data={"name": "test", "training_config": {"framework": "pytorch"}},
        )

        # 验证传给 create 的实体 visibility 为 PRIVATE
        call_args = mock_template_repository.create.call_args
        entity = call_args[0][0]
        assert entity.visibility == TemplateVisibility.PRIVATE

    async def test_create_template_duplicate_name_raises_error(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
    ) -> None:
        """同一 owner 下重复名称抛出 DuplicateEntityError。"""
        mock_template_repository.exists_by_name_and_owner.return_value = True

        with pytest.raises(DuplicateEntityError):
            await service.create_template(
                owner_id=10,
                data={
                    "name": "duplicate-name",
                    "training_config": {"framework": "pytorch"},
                },
            )


# ==================== get_template ====================


class TestGetTemplate:
    """测试获取模板。"""

    async def test_get_template_owner_success(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        sample_template: JobTemplate,
    ) -> None:
        """Owner 可以查看自己的私有模板。"""
        mock_template_repository.get_by_id.return_value = sample_template

        result = await service.get_template(template_id=1, user_id=10)

        assert result.id == 1
        assert result.name == "test-template"

    async def test_get_template_not_found_raises_error(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
    ) -> None:
        """模板不存在抛出 JobTemplateNotFoundError。"""
        mock_template_repository.get_by_id.return_value = None

        with pytest.raises(JobTemplateNotFoundError):
            await service.get_template(template_id=999, user_id=10)

    async def test_get_private_template_other_user_raises_error(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        sample_template: JobTemplate,
    ) -> None:
        """非 owner 用户查看私有模板抛出权限错误。"""
        mock_template_repository.get_by_id.return_value = sample_template

        with pytest.raises(JobTemplatePermissionDeniedError):
            await service.get_template(template_id=1, user_id=99)

    async def test_get_public_template_other_user_success(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        public_template: JobTemplate,
    ) -> None:
        """任何用户可以查看公开模板。"""
        mock_template_repository.get_by_id.return_value = public_template

        result = await service.get_template(template_id=2, user_id=99)

        assert result.id == 2
        assert result.visibility == TemplateVisibility.PUBLIC


# ==================== update_template ====================


class TestUpdateTemplate:
    """测试更新模板。"""

    async def test_update_template_name_success(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        sample_template: JobTemplate,
    ) -> None:
        """Owner 可以更新模板名称。"""
        mock_template_repository.get_by_id.return_value = sample_template
        mock_template_repository.update.return_value = sample_template

        result = await service.update_template(
            template_id=1,
            user_id=10,
            data={"name": "updated-name"},
        )

        mock_template_repository.exists_by_name_and_owner.assert_called_once_with("updated-name", 10)
        mock_template_repository.update.assert_called_once()

    async def test_update_template_description(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        sample_template: JobTemplate,
    ) -> None:
        """更新模板描述。"""
        mock_template_repository.get_by_id.return_value = sample_template
        mock_template_repository.update.return_value = sample_template

        await service.update_template(
            template_id=1,
            user_id=10,
            data={"description": "新描述"},
        )

        mock_template_repository.update.assert_called_once()

    async def test_update_template_visibility(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        sample_template: JobTemplate,
    ) -> None:
        """更新模板可见性。"""
        mock_template_repository.get_by_id.return_value = sample_template
        mock_template_repository.update.return_value = sample_template

        await service.update_template(
            template_id=1,
            user_id=10,
            data={"visibility": "PUBLIC"},
        )

        mock_template_repository.update.assert_called_once()

    async def test_update_template_training_config(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        sample_template: JobTemplate,
    ) -> None:
        """更新训练配置。"""
        mock_template_repository.get_by_id.return_value = sample_template
        mock_template_repository.update.return_value = sample_template

        await service.update_template(
            template_id=1,
            user_id=10,
            data={"training_config": {"framework": "deepspeed", "gpu_count": 8}},
        )

        mock_template_repository.update.assert_called_once()

    async def test_update_template_not_found(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
    ) -> None:
        """更新不存在的模板抛出错误。"""
        mock_template_repository.get_by_id.return_value = None

        with pytest.raises(JobTemplateNotFoundError):
            await service.update_template(
                template_id=999,
                user_id=10,
                data={"name": "new-name"},
            )

    async def test_update_template_permission_denied(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        sample_template: JobTemplate,
    ) -> None:
        """非 owner 更新模板抛出权限错误。"""
        mock_template_repository.get_by_id.return_value = sample_template

        with pytest.raises(JobTemplatePermissionDeniedError):
            await service.update_template(
                template_id=1,
                user_id=99,
                data={"name": "new-name"},
            )

    async def test_update_template_duplicate_name_raises_error(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        sample_template: JobTemplate,
    ) -> None:
        """更新为已存在的名称抛出 DuplicateEntityError。"""
        mock_template_repository.get_by_id.return_value = sample_template
        mock_template_repository.exists_by_name_and_owner.return_value = True

        with pytest.raises(DuplicateEntityError):
            await service.update_template(
                template_id=1,
                user_id=10,
                data={"name": "existing-name"},
            )

    async def test_update_template_same_name_no_duplicate_check(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        sample_template: JobTemplate,
    ) -> None:
        """更新为相同名称不触发重复检查。"""
        mock_template_repository.get_by_id.return_value = sample_template
        mock_template_repository.update.return_value = sample_template

        await service.update_template(
            template_id=1,
            user_id=10,
            data={"name": "test-template"},  # 和当前名称相同
        )

        mock_template_repository.exists_by_name_and_owner.assert_not_called()


# ==================== delete_template ====================


class TestDeleteTemplate:
    """测试删除模板。"""

    async def test_delete_template_success(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        sample_template: JobTemplate,
    ) -> None:
        """Owner 可以软删除模板。"""
        mock_template_repository.get_by_id.return_value = sample_template

        await service.delete_template(template_id=1, user_id=10)

        mock_template_repository.soft_delete.assert_called_once_with(1)

    async def test_delete_template_not_found(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
    ) -> None:
        """删除不存在的模板抛出错误。"""
        mock_template_repository.get_by_id.return_value = None

        with pytest.raises(JobTemplateNotFoundError):
            await service.delete_template(template_id=999, user_id=10)

    async def test_delete_template_permission_denied(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        sample_template: JobTemplate,
    ) -> None:
        """非 owner 删除模板抛出权限错误。"""
        mock_template_repository.get_by_id.return_value = sample_template

        with pytest.raises(JobTemplatePermissionDeniedError):
            await service.delete_template(template_id=1, user_id=99)


# ==================== list_visible_templates ====================


class TestListVisibleTemplates:
    """测试列表查询。"""

    async def test_list_visible_templates_delegates_to_repository(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        sample_template: JobTemplate,
    ) -> None:
        """列表查询委托给 repository。"""
        mock_template_repository.list_visible_templates.return_value = ([sample_template], 1)

        templates, total = await service.list_visible_templates(user_id=10)

        assert len(templates) == 1
        assert total == 1
        mock_template_repository.list_visible_templates.assert_called_once_with(
            user_id=10,
            search_name=None,
            page=1,
            page_size=20,
            sort_by="usage_count",
            sort_order="desc",
        )

    async def test_list_visible_templates_with_search(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
    ) -> None:
        """带搜索条件的列表查询。"""
        mock_template_repository.list_visible_templates.return_value = ([], 0)

        await service.list_visible_templates(user_id=10, search_name="pytorch")

        mock_template_repository.list_visible_templates.assert_called_once_with(
            user_id=10,
            search_name="pytorch",
            page=1,
            page_size=20,
            sort_by="usage_count",
            sort_order="desc",
        )


# ==================== get_popular_templates ====================


class TestGetPopularTemplates:
    """测试获取热门模板。"""

    async def test_get_popular_templates(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
        public_template: JobTemplate,
    ) -> None:
        """获取热门公开模板。"""
        mock_template_repository.get_popular_templates.return_value = [public_template]

        result = await service.get_popular_templates(limit=5)

        assert len(result) == 1
        mock_template_repository.get_popular_templates.assert_called_once_with(5)


# ==================== increment_usage ====================


class TestIncrementUsage:
    """测试使用次数递增。"""

    async def test_increment_usage(
        self,
        service: JobTemplateService,
        mock_template_repository: AsyncMock,
    ) -> None:
        """递增模板使用次数。"""
        await service.increment_usage(template_id=1)

        mock_template_repository.increment_usage_count.assert_called_once_with(1)
