"""Job Template Service - Business logic for job template management."""

from src.modules.training.domain.entities import JobTemplate
from src.modules.training.domain.exceptions import (
    JobTemplateNotFoundError,
    JobTemplatePermissionDeniedError,
)
from src.modules.training.domain.repositories import IJobTemplateRepository
from src.modules.training.domain.value_objects import TemplateVisibility
from src.shared.application.enhanced_base_service import EnhancedBaseService
from src.shared.domain.exceptions import DuplicateEntityError
from src.shared.utils import EnumMapper


class JobTemplateService(EnhancedBaseService[JobTemplate, int]):
    """Service for managing job templates."""

    def __init__(self, repository: IJobTemplateRepository):
        super().__init__(repository, "JobTemplate")
        self._not_found_error_factory = JobTemplateNotFoundError

    async def create_template(self, owner_id: int, data: dict) -> JobTemplate:
        """Create a new job template."""
        name = data["name"]

        # Check for duplicate name for the same owner
        if await self._repository.exists_by_name_and_owner(name, owner_id):
            raise DuplicateEntityError("JobTemplate", f"name={name}")

        # Convert visibility enum
        visibility = EnumMapper.from_string(
            data.get("visibility", "PRIVATE"),
            TemplateVisibility,
            TemplateVisibility.PRIVATE,
        )

        # Create domain entity
        template = JobTemplate(
            id=0,  # Will be assigned by database
            name=name,
            owner_id=owner_id,
            training_config=data["training_config"],
            description=data.get("description"),
            visibility=visibility,
        )

        return await self._repository.create(template)

    async def get_template(self, template_id: int, user_id: int) -> JobTemplate:
        """Get a template by ID with visibility check."""
        template = await self._repository.get_by_id(template_id)
        if not template:
            raise JobTemplateNotFoundError(template_id)

        if not template.is_visible_to(user_id):
            raise JobTemplatePermissionDeniedError("view", template_id)

        return template

    async def update_template(
        self, template_id: int, user_id: int, data: dict
    ) -> JobTemplate:
        """Update a template (owner only)."""
        template = await self._repository.get_by_id(template_id)
        if not template:
            raise JobTemplateNotFoundError(template_id)

        if not template.can_modify(user_id):
            raise JobTemplatePermissionDeniedError("modify", template_id)

        # Update fields if provided
        if "name" in data and data["name"] is not None:
            # Check for duplicate name if changing
            if data["name"] != template.name:
                if await self._repository.exists_by_name_and_owner(
                    data["name"], user_id
                ):
                    raise DuplicateEntityError("JobTemplate", f"name={data['name']}")
            template.update_name(data["name"])

        if "description" in data:
            template.update_description(data["description"])

        if "visibility" in data and data["visibility"] is not None:
            visibility = EnumMapper.from_string(
                data["visibility"],
                TemplateVisibility,
                template.visibility,
            )
            template.update_visibility(visibility)

        if "training_config" in data and data["training_config"] is not None:
            template.update_training_config(data["training_config"])

        return await self._repository.update(template)

    async def delete_template(self, template_id: int, user_id: int) -> None:
        """Soft delete a template (owner only)."""
        template = await self._repository.get_by_id(template_id)
        if not template:
            raise JobTemplateNotFoundError(template_id)

        if not template.can_modify(user_id):
            raise JobTemplatePermissionDeniedError("delete", template_id)

        await self._repository.soft_delete(template_id)

    async def list_visible_templates(
        self,
        user_id: int,
        search_name: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "usage_count",
        sort_order: str = "desc",
    ) -> tuple[list[JobTemplate], int]:
        """List templates visible to the user."""
        return await self._repository.list_visible_templates(
            user_id=user_id,
            search_name=search_name,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def get_popular_templates(self, limit: int = 10) -> list[JobTemplate]:
        """Get most popular public templates."""
        return await self._repository.get_popular_templates(limit)

    async def increment_usage(self, template_id: int) -> None:
        """Increment template usage count."""
        await self._repository.increment_usage_count(template_id)
