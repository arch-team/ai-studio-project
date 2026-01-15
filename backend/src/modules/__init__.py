"""Feature Modules - Business domain modules.

Each module is a self-contained unit with:
- api: HTTP endpoints, schemas, dependencies
- application: Business services
- domain: Entities, value objects, repositories
- infrastructure: ORM models, repository implementations

Modules:
- auth: Authentication and authorization
- training: Training job management
- models: Model registry
- quotas: Resource quota management
- datasets: Dataset version control
- spaces: Development environments
- monitoring: Cluster monitoring
- billing: Cost analysis
- audit: Audit logging
"""

__all__: list[str] = []
