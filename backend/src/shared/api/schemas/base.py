"""Base schema classes for entity-schema conversion."""

from typing import Any, Generic, Self, TypeVar

from pydantic import BaseModel

Entity = TypeVar("Entity")


class EntitySchema(BaseModel, Generic[Entity]):
    """Base schema with entity conversion support.

    Subclasses should implement _map_entity_fields() to define
    the mapping from domain entity to schema fields.

    Example:
        class TrainingJobSummary(EntitySchema["TrainingJob"]):
            id: int
            job_name: str
            status: JobStatusEnum

            @classmethod
            def _map_entity_fields(cls, entity: TrainingJob) -> dict:
                return {
                    "id": entity.id,
                    "job_name": entity.job_name,
                    "status": EnumMapper.to_api(entity.status, JobStatusEnum),
                }

        # Usage in endpoint:
        summary = TrainingJobSummary.from_entity(job, owner_username="alice")
    """

    @classmethod
    def from_entity(cls, entity: Entity, **extra_fields: Any) -> Self:
        """Create schema instance from domain entity.

        Args:
            entity: Domain entity instance
            **extra_fields: Additional fields not on the entity (e.g., owner_username)

        Returns:
            Schema instance with mapped fields
        """
        fields = cls._map_entity_fields(entity)
        fields.update(extra_fields)
        return cls(**fields)

    @classmethod
    def _map_entity_fields(cls, entity: Entity) -> dict[str, Any]:
        """Map entity fields to schema fields.

        Subclasses must override this method to define field mappings.
        Use EnumMapper for enum conversions.
        """
        raise NotImplementedError(f"{cls.__name__} must implement _map_entity_fields()")
