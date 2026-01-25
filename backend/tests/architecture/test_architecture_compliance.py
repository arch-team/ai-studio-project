"""Architecture compliance tests - Verify Clean Architecture dependency rules.

This test ensures that the application layer does not directly import
infrastructure layer modules, maintaining proper dependency direction:
    API → Application → Domain ← Infrastructure

Modular Monolith Rules (see docs/module-dependency-spec.md):
    R1: Module Domain layer MUST NOT import any other module code
    R2: Module Application layer MUST only depend on interfaces, not implementations
    R3: Cross-module communication MUST use EventBus or shared interfaces
    R4: Auth module authentication dependencies are the ONLY exception (API layer only)
"""

import ast
import os
from pathlib import Path

import pytest


def get_python_files(directory: Path) -> list[Path]:
    """Get all Python files in directory recursively."""
    return list(directory.rglob("*.py"))


def get_imports_from_file(file_path: Path, include_type_checking: bool = False) -> list[str]:
    """Extract all import statements from a Python file.

    Args:
        file_path: Path to the Python file
        include_type_checking: If False, exclude imports inside TYPE_CHECKING blocks

    Returns:
        List of import module names
    """
    imports = []
    try:
        with open(file_path, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        # 找出所有 TYPE_CHECKING 块的位置
        type_checking_ranges: list[tuple[int, int]] = []
        if not include_type_checking:
            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    # 检查条件是否为 TYPE_CHECKING
                    if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
                        type_checking_ranges.append((node.lineno, node.end_lineno or node.lineno))

        def is_in_type_checking(lineno: int) -> bool:
            """检查行号是否在 TYPE_CHECKING 块内."""
            return any(start <= lineno <= end for start, end in type_checking_ranges)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if include_type_checking or not is_in_type_checking(node.lineno):
                    for alias in node.names:
                        imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if include_type_checking or not is_in_type_checking(node.lineno):
                        imports.append(node.module)
    except SyntaxError:
        pass
    return imports


class TestApplicationLayerDoesNotImportInfrastructure:
    """Test that application layer does not import infrastructure models."""

    @pytest.fixture
    def backend_src_path(self) -> Path:
        """Get the backend src path."""
        # Navigate from tests/unit/ to backend/src/
        current = Path(__file__).parent
        return current.parent.parent / "src"

    @pytest.fixture
    def application_files(self, backend_src_path: Path) -> list[Path]:
        """Get all Python files in application layer."""
        app_path = backend_src_path / "application"
        return get_python_files(app_path)

    def test_application_services_do_not_import_infrastructure_models(
        self, application_files: list[Path]
    ):
        """Application services should not import infrastructure persistence models.

        Violation of this rule indicates that the application layer is tightly
        coupled to the infrastructure layer, breaking Clean Architecture.
        """
        violations = []

        for file_path in application_files:
            imports = get_imports_from_file(file_path)

            for imp in imports:
                # Check for direct infrastructure model imports
                if "infrastructure.persistence.models" in imp:
                    violations.append(
                        f"{file_path.relative_to(file_path.parent.parent.parent)}: "
                        f"imports '{imp}'"
                    )

        assert not violations, (
            f"Application layer should not import infrastructure models.\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_application_services_do_not_use_sqlalchemy_select(
        self, application_files: list[Path]
    ):
        """Application services should not use SQLAlchemy select directly.

        Database queries should be encapsulated in repository implementations.
        """
        violations = []

        for file_path in application_files:
            imports = get_imports_from_file(file_path)

            for imp in imports:
                if imp == "sqlalchemy" or imp.startswith("sqlalchemy."):
                    if "ext.asyncio" not in imp:  # Allow AsyncSession type hint
                        violations.append(
                            f"{file_path.relative_to(file_path.parent.parent.parent)}: "
                            f"imports '{imp}'"
                        )

        # Note: This test may need adjustment based on your specific rules
        # For now, we allow AsyncSession for dependency injection
        sqlalchemy_query_imports = [
            v for v in violations if "select" in v.lower() or "sqlalchemy" in v.lower()
        ]

        if sqlalchemy_query_imports:
            # Filter out acceptable imports (AsyncSession for DI)
            actual_violations = [
                v
                for v in sqlalchemy_query_imports
                if "ext.asyncio" not in v and "AsyncSession" not in v
            ]

            if actual_violations:
                assert False, (
                    f"Application layer should not use SQLAlchemy queries directly.\n"
                    f"Found violation(s):\n"
                    + "\n".join(f"  - {v}" for v in actual_violations)
                )


class TestDomainLayerIndependence:
    """Test that domain layer has no external dependencies."""

    @pytest.fixture
    def backend_src_path(self) -> Path:
        """Get the backend src path."""
        current = Path(__file__).parent
        return current.parent.parent / "src"

    @pytest.fixture
    def domain_files(self, backend_src_path: Path) -> list[Path]:
        """Get all Python files in domain layer."""
        domain_path = backend_src_path / "domain"
        return get_python_files(domain_path)

    def test_domain_layer_does_not_import_infrastructure(
        self, domain_files: list[Path]
    ):
        """Domain layer should not import infrastructure modules."""
        violations = []

        for file_path in domain_files:
            imports = get_imports_from_file(file_path)

            for imp in imports:
                if "infrastructure" in imp:
                    violations.append(
                        f"{file_path.relative_to(file_path.parent.parent.parent)}: "
                        f"imports '{imp}'"
                    )

        assert not violations, (
            f"Domain layer should not import infrastructure modules.\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_domain_layer_does_not_import_api(self, domain_files: list[Path]):
        """Domain layer should not import API modules."""
        violations = []

        for file_path in domain_files:
            imports = get_imports_from_file(file_path)

            for imp in imports:
                if "api." in imp or imp.startswith("src.api"):
                    violations.append(
                        f"{file_path.relative_to(file_path.parent.parent.parent)}: "
                        f"imports '{imp}'"
                    )

        assert not violations, (
            f"Domain layer should not import API modules.\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestApiLayerDoesNotImportInfrastructureModels:
    """Test that API layer does not directly import infrastructure ORM models.

    API endpoints should use services/repositories, not ORM models directly.
    """

    @pytest.fixture
    def backend_src_path(self) -> Path:
        """Get the backend src path."""
        current = Path(__file__).parent
        return current.parent.parent / "src"

    @pytest.fixture
    def api_endpoint_files(self, backend_src_path: Path) -> list[Path]:
        """Get all Python files in API endpoints."""
        api_path = backend_src_path / "api" / "v1" / "endpoints"
        return get_python_files(api_path)

    def test_api_endpoints_do_not_import_orm_models(
        self, api_endpoint_files: list[Path]
    ):
        """API endpoints should not import infrastructure ORM models.

        Endpoints should work with domain entities through services,
        not directly with ORM models.
        """
        violations = []

        for file_path in api_endpoint_files:
            imports = get_imports_from_file(file_path)

            for imp in imports:
                # Check for direct ORM model imports
                if "infrastructure.persistence.models" in imp:
                    violations.append(
                        f"{file_path.name}: imports '{imp}'"
                    )

        assert not violations, (
            f"API endpoints should not import infrastructure ORM models.\n"
            f"Use services/repositories instead of direct ORM access.\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_api_endpoints_do_not_use_session_add(
        self, api_endpoint_files: list[Path]
    ):
        """API endpoints should not call session.add() directly.

        Database writes should be encapsulated in services/repositories.
        """
        violations = []

        for file_path in api_endpoint_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Look for session.add() calls (but not in comments)
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if "session.add(" in line:
                        violations.append(
                            f"{file_path.name}:{i}: contains 'session.add()'"
                        )
            except Exception:
                pass

        assert not violations, (
            f"API endpoints should not call session.add() directly.\n"
            f"Database writes should go through services/repositories.\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestDomainExceptionUsage:
    """Test that domain entities use domain exceptions instead of ValueError."""

    @pytest.fixture
    def backend_src_path(self) -> Path:
        """Get the backend src path."""
        current = Path(__file__).parent
        return current.parent.parent / "src"

    @pytest.fixture
    def domain_entity_files(self, backend_src_path: Path) -> list[Path]:
        """Get all Python files in domain entities."""
        entities_path = backend_src_path / "domain" / "entities"
        return get_python_files(entities_path)

    def test_domain_entities_do_not_use_valueerror_for_state_transitions(
        self, domain_entity_files: list[Path]
    ):
        """Domain entities should use InvalidStateTransitionError, not ValueError.

        State transition errors are domain-specific and should be expressed
        using domain exceptions for better error handling and API responses.
        """
        violations = []

        for file_path in domain_entity_files:
            if file_path.name == "__init__.py":
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    # Check for ValueError usage in state transition context
                    if "raise ValueError" in line:
                        violations.append(
                            f"{file_path.name}:{i}: uses ValueError instead of domain exception"
                        )
            except Exception:
                pass

        assert not violations, (
            f"Domain entities should use domain exceptions (e.g., InvalidStateTransitionError).\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestMiddlewareExecutionOrder:
    """Test that middleware is configured in the correct execution order.

    Starlette middleware uses LIFO (Last In, First Out) order:
    - Last added middleware executes first (on request)
    - First added middleware executes last (on request)

    Correct execution order (request entering):
    1. CORSMiddleware - Handle preflight requests
    2. AuthenticationMiddleware - Validate JWT, set request.state.user_id
    3. AuditMiddleware - Log audit events (needs user info from auth)
    """

    def test_middleware_order_audit_after_auth(self):
        """AuditMiddleware should execute after AuthenticationMiddleware.

        Since Starlette uses LIFO, AuditMiddleware should be added BEFORE
        AuthenticationMiddleware in the code.
        """
        import inspect

        from src.main import create_app

        source = inspect.getsource(create_app)

        # Find positions of add_middleware calls in the function body
        # We need to find the actual add_middleware calls, not imports
        audit_add_pos = source.find("add_middleware(AuditMiddleware")
        auth_add_pos = source.find("add_middleware(AuthenticationMiddleware")
        cors_add_pos = source.find("add_middleware")  # First occurrence is CORS

        # For correct LIFO execution order (CORS -> Auth -> Audit on request),
        # the add order in code should be: Audit -> Auth -> CORS
        # Which means: audit_add_pos < auth_add_pos < cors_add_pos in the source
        assert audit_add_pos != -1, "AuditMiddleware add_middleware call not found"
        assert auth_add_pos != -1, "AuthenticationMiddleware add_middleware call not found"

        assert audit_add_pos < auth_add_pos, (
            "AuditMiddleware should be added BEFORE AuthenticationMiddleware.\n"
            "Starlette middleware uses LIFO order, so to execute Audit AFTER Auth,\n"
            "Audit must be added first in the code.\n"
            f"Found: audit_pos={audit_add_pos}, auth_pos={auth_add_pos}"
        )


class TestCorsConfiguration:
    """Test that CORS configuration is properly restricted."""

    def test_cors_does_not_allow_all_methods(self):
        """CORS should not allow all HTTP methods with wildcard.

        Using allow_methods=["*"] is a security risk as it allows
        any HTTP method including potentially dangerous ones.
        """
        import inspect

        from src.main import create_app

        source = inspect.getsource(create_app)

        # Check for overly permissive method configuration
        assert 'allow_methods=["*"]' not in source, (
            "CORS should not use allow_methods=['*'].\n"
            "Explicitly list allowed methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']"
        )

    def test_cors_does_not_allow_all_headers(self):
        """CORS should not allow all headers with wildcard.

        Using allow_headers=["*"] is a security risk.
        """
        import inspect

        from src.main import create_app

        source = inspect.getsource(create_app)

        # Check for overly permissive header configuration
        assert 'allow_headers=["*"]' not in source, (
            "CORS should not use allow_headers=['*'].\n"
            "Explicitly list allowed headers: ['Content-Type', 'Authorization', ...]"
        )


class TestApiErrorResponseConsistency:
    """Test that API error responses use a consistent schema.

    All error responses should use the unified ErrorResponse from common.py.
    """

    @pytest.fixture
    def backend_src_path(self) -> Path:
        """Get the backend src path."""
        current = Path(__file__).parent
        return current.parent.parent / "src"

    @pytest.fixture
    def api_schema_files(self, backend_src_path: Path) -> list[Path]:
        """Get all Python files in API schemas."""
        schema_path = backend_src_path / "api" / "v1" / "schemas"
        return get_python_files(schema_path)

    def test_error_response_defined_only_in_common(
        self, api_schema_files: list[Path]
    ):
        """ErrorResponse should only be defined in common.py.

        All other schema files should import from common.py.
        """
        violations = []

        for file_path in api_schema_files:
            if file_path.name == "common.py":
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Check for local ErrorResponse class definition
                if "class ErrorResponse" in content:
                    violations.append(
                        f"{file_path.name}: defines its own ErrorResponse class"
                    )
            except Exception:
                pass

        assert not violations, (
            f"ErrorResponse should only be defined in common.py.\n"
            f"Other schema files should import from common.py.\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_middleware_uses_consistent_error_format(
        self, backend_src_path: Path
    ):
        """Middleware should use consistent error response format.

        All error responses should use 'code' field, not 'error'.
        """
        middleware_path = backend_src_path / "api" / "middleware"
        violations = []

        for file_path in get_python_files(middleware_path):
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Look for inconsistent error format (using 'error' instead of 'code')
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    if '"error":' in line and "JSONResponse" in content:
                        violations.append(
                            f"{file_path.name}:{i}: uses 'error' instead of 'code'"
                        )
            except Exception:
                pass

        assert not violations, (
            f"Middleware should use 'code' field for error responses.\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestApiStateTransitionEndpoints:
    """Test that API uses dedicated endpoints for state transitions.

    RESTful best practice: State transitions should use dedicated action endpoints
    instead of generic PATCH with action parameter.

    Bad:  PATCH /training-jobs/{id}  body: {"action": "pause"}
    Good: POST  /training-jobs/{id}/pause
    """

    @pytest.fixture
    def backend_src_path(self) -> Path:
        """Get the backend src path."""
        current = Path(__file__).parent
        return current.parent.parent / "src"

    def test_training_jobs_has_dedicated_pause_endpoint(
        self, backend_src_path: Path
    ):
        """Training jobs API should have a dedicated POST /pause endpoint."""
        # Updated path for modular architecture
        endpoint_file = (
            backend_src_path / "modules" / "training" / "api" / "endpoints.py"
        )

        with open(endpoint_file, encoding="utf-8") as f:
            content = f.read()

        # Check for dedicated pause endpoint
        assert '/{job_id}/pause' in content or "/{job_id}/pause" in content, (
            "Training jobs API should have a dedicated POST /{job_id}/pause endpoint.\n"
            "State transitions should use dedicated action endpoints, not generic PATCH."
        )

    def test_training_jobs_has_dedicated_resume_endpoint(
        self, backend_src_path: Path
    ):
        """Training jobs API should have a dedicated POST /resume endpoint."""
        # Updated path for modular architecture
        endpoint_file = (
            backend_src_path / "modules" / "training" / "api" / "endpoints.py"
        )

        with open(endpoint_file, encoding="utf-8") as f:
            content = f.read()

        # Check for dedicated resume endpoint
        assert '/{job_id}/resume' in content or "/{job_id}/resume" in content, (
            "Training jobs API should have a dedicated POST /{job_id}/resume endpoint.\n"
            "State transitions should use dedicated action endpoints, not generic PATCH."
        )

    def test_training_jobs_has_dedicated_cancel_endpoint(
        self, backend_src_path: Path
    ):
        """Training jobs API should have a dedicated POST /cancel endpoint."""
        # Updated path for modular architecture
        endpoint_file = (
            backend_src_path / "modules" / "training" / "api" / "endpoints.py"
        )

        with open(endpoint_file, encoding="utf-8") as f:
            content = f.read()

        # Check for dedicated cancel endpoint
        assert '/{job_id}/cancel' in content or "/{job_id}/cancel" in content, (
            "Training jobs API should have a dedicated POST /{job_id}/cancel endpoint.\n"
            "State transitions should use dedicated action endpoints, not generic PATCH."
        )

    def test_no_generic_action_parameter_in_update_request(
        self, backend_src_path: Path
    ):
        """UpdateTrainingJobRequest should not use generic action parameter.

        The action parameter pattern indicates mixing multiple operations
        in a single endpoint, which reduces API clarity.
        """
        # Updated path for modular architecture
        schema_file = (
            backend_src_path / "modules" / "training" / "api" / "schemas" / "requests.py"
        )

        with open(schema_file, encoding="utf-8") as f:
            content = f.read()

        # Check that UpdateTrainingJobRequest doesn't use action field for state transitions
        # We look for Literal["pause", "resume", "cancel"] pattern which indicates
        # the anti-pattern of using a single endpoint for multiple state transitions
        has_action_literal = (
            'Literal["pause", "resume", "cancel"]' in content
            or "Literal['pause', 'resume', 'cancel']" in content
        )

        assert not has_action_literal, (
            "UpdateTrainingJobRequest should not use action: Literal['pause', 'resume', 'cancel'].\n"
            "State transitions should use dedicated endpoints instead of generic action parameter."
        )


# =============================================================================
# Modular Monolith Module Dependency Compliance Tests
# =============================================================================


class TestModuleDomainLayerIsolation:
    """Test R1: Module Domain layer MUST NOT import any other module code.

    Domain layer should only depend on:
    - Python standard library
    - shared/domain/* (base entities, exceptions, events)
    - Same module's domain code

    Domain layer MUST NOT import:
    - Other modules' code (modules.xxx where xxx != current_module)
    - Infrastructure layer
    - API layer
    """

    @pytest.fixture
    def backend_src_path(self) -> Path:
        """Get the backend src path."""
        current = Path(__file__).parent
        return current.parent.parent / "src"

    @pytest.fixture
    def module_domain_files(self, backend_src_path: Path) -> list[tuple[str, Path]]:
        """Get all Python files in module domain layers with module name."""
        modules_path = backend_src_path / "modules"
        result = []
        for module_dir in modules_path.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith("_"):
                domain_path = module_dir / "domain"
                if domain_path.exists():
                    for py_file in domain_path.rglob("*.py"):
                        result.append((module_dir.name, py_file))
        return result

    def test_domain_layer_no_cross_module_imports(
        self, module_domain_files: list[tuple[str, Path]]
    ):
        """Module domain layer should not import from other modules.

        Allowed:
        - src.shared.domain.*
        - src.modules.<same_module>.domain.*

        Forbidden:
        - src.modules.<other_module>.*
        """
        violations = []

        for module_name, file_path in module_domain_files:
            if file_path.name == "__init__.py":
                continue

            imports = get_imports_from_file(file_path)

            for imp in imports:
                # Check for cross-module imports
                if "src.modules." in imp:
                    # Extract the imported module name
                    parts = imp.split(".")
                    if len(parts) >= 3 and parts[1] == "modules":
                        imported_module = parts[2]
                        if imported_module != module_name:
                            violations.append(
                                f"{module_name}/domain/{file_path.name}: "
                                f"imports '{imp}' (cross-module dependency)"
                            )

        assert not violations, (
            "Module domain layer MUST NOT import from other modules.\n"
            "See docs/module-dependency-spec.md Rule R1.\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestModuleApplicationLayerDependencies:
    """Test R2: Module Application layer dependency rules.

    Application layer should only depend on:
    - Domain layer interfaces (IRepository, etc.)
    - shared/* (infrastructure, domain, utils)
    - Same module's code

    Application layer MUST NOT import:
    - Other modules' services directly
    - Other modules' repository implementations
    """

    @pytest.fixture
    def backend_src_path(self) -> Path:
        """Get the backend src path."""
        current = Path(__file__).parent
        return current.parent.parent / "src"

    @pytest.fixture
    def module_application_files(self, backend_src_path: Path) -> list[tuple[str, Path]]:
        """Get all Python files in module application layers with module name."""
        modules_path = backend_src_path / "modules"
        result = []
        for module_dir in modules_path.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith("_"):
                app_path = module_dir / "application"
                if app_path.exists():
                    for py_file in app_path.rglob("*.py"):
                        result.append((module_dir.name, py_file))
        return result

    def test_no_cross_module_service_imports(
        self, module_application_files: list[tuple[str, Path]]
    ):
        """Application layer should not import other modules' services.

        Cross-module communication should use:
        - EventBus for async decoupling
        - Shared interfaces for sync calls
        """
        violations = []

        for module_name, file_path in module_application_files:
            if file_path.name == "__init__.py":
                continue

            imports = get_imports_from_file(file_path)

            for imp in imports:
                # Check for cross-module service imports
                if "src.modules." in imp and ".application." in imp:
                    parts = imp.split(".")
                    if len(parts) >= 3 and parts[1] == "modules":
                        imported_module = parts[2]
                        if imported_module != module_name:
                            violations.append(
                                f"{module_name}/application/{file_path.name}: "
                                f"imports '{imp}' (cross-module service dependency)"
                            )

        assert not violations, (
            "Application layer MUST NOT import other modules' services directly.\n"
            "Use EventBus or shared interfaces for cross-module communication.\n"
            "See docs/module-dependency-spec.md Rule R3.\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_no_cross_module_repository_impl_imports(
        self, module_application_files: list[tuple[str, Path]]
    ):
        """Application layer should not import other modules' repository implementations.

        Application services should depend on repository interfaces (IRepository),
        not concrete implementations.
        """
        violations = []

        for module_name, file_path in module_application_files:
            if file_path.name == "__init__.py":
                continue

            imports = get_imports_from_file(file_path)

            for imp in imports:
                # Check for cross-module infrastructure imports
                if "src.modules." in imp and ".infrastructure." in imp:
                    parts = imp.split(".")
                    if len(parts) >= 3 and parts[1] == "modules":
                        imported_module = parts[2]
                        if imported_module != module_name:
                            violations.append(
                                f"{module_name}/application/{file_path.name}: "
                                f"imports '{imp}' (cross-module infrastructure dependency)"
                            )

        assert not violations, (
            "Application layer MUST NOT import other modules' infrastructure.\n"
            "Depend on interfaces, not implementations.\n"
            "See docs/module-dependency-spec.md Rule R2.\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestModuleApiLayerAuthDependency:
    """Test R4: Auth module dependency exception.

    Only API layer can import auth module's authentication dependencies.
    Other layers (domain, application) MUST NOT import from auth module.

    Exception: ORM models in infrastructure layer may import UserModel
    for foreign key relationships - this is a SQLAlchemy technical requirement.
    """

    @pytest.fixture
    def backend_src_path(self) -> Path:
        """Get the backend src path."""
        current = Path(__file__).parent
        return current.parent.parent / "src"

    @pytest.fixture
    def non_api_module_files(self, backend_src_path: Path) -> list[tuple[str, str, Path]]:
        """Get all non-API Python files in modules with module name and layer."""
        modules_path = backend_src_path / "modules"
        result = []
        for module_dir in modules_path.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith("_"):
                # Skip auth module itself
                if module_dir.name == "auth":
                    continue
                for layer in ["domain", "application"]:  # Exclude infrastructure
                    layer_path = module_dir / layer
                    if layer_path.exists():
                        for py_file in layer_path.rglob("*.py"):
                            result.append((module_dir.name, layer, py_file))
        return result

    def test_only_api_layer_imports_auth(
        self, non_api_module_files: list[tuple[str, str, Path]]
    ):
        """Only API layer should import auth module dependencies.

        Domain and Application layers should not depend on auth module
        to maintain proper separation of concerns.

        Note: Infrastructure ORM models are excluded as they may need
        UserModel for foreign key relationships.
        """
        violations = []

        for module_name, layer, file_path in non_api_module_files:
            if file_path.name == "__init__.py":
                continue

            imports = get_imports_from_file(file_path)

            for imp in imports:
                if "src.modules.auth" in imp:
                    violations.append(
                        f"{module_name}/{layer}/{file_path.name}: "
                        f"imports '{imp}' (auth import outside API layer)"
                    )

        assert not violations, (
            "Only API layer can import auth module dependencies.\n"
            "Domain/Application layers should not import auth.\n"
            "See docs/module-dependency-spec.md Rule R4.\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestModuleInfrastructureLayerIsolation:
    """Test that infrastructure layer does not import from other modules' infrastructure."""

    @pytest.fixture
    def backend_src_path(self) -> Path:
        """Get the backend src path."""
        current = Path(__file__).parent
        return current.parent.parent / "src"

    @pytest.fixture
    def module_infrastructure_files(self, backend_src_path: Path) -> list[tuple[str, Path]]:
        """Get all Python files in module infrastructure layers."""
        modules_path = backend_src_path / "modules"
        result = []
        for module_dir in modules_path.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith("_"):
                infra_path = module_dir / "infrastructure"
                if infra_path.exists():
                    for py_file in infra_path.rglob("*.py"):
                        result.append((module_dir.name, py_file))
        return result

    def test_no_cross_module_infrastructure_imports(
        self, module_infrastructure_files: list[tuple[str, Path]]
    ):
        """Infrastructure layer should not import from other modules' infrastructure.

        Each module's infrastructure should be self-contained.
        Shared infrastructure belongs in shared/infrastructure/.

        Exception: ORM model files (*_model.py) are allowed to import other modules'
        ORM models for SQLAlchemy foreign key relationships. This is a technical
        necessity for defining database relationships.
        See: docs/ARCHITECTURE.md Section 3.3
        """
        violations = []

        for module_name, file_path in module_infrastructure_files:
            if file_path.name == "__init__.py":
                continue

            # Exception: ORM model files can import other modules' models
            # for SQLAlchemy foreign key relationships
            if file_path.name.endswith("_model.py"):
                continue

            imports = get_imports_from_file(file_path)

            for imp in imports:
                if "src.modules." in imp and ".infrastructure." in imp:
                    parts = imp.split(".")
                    if len(parts) >= 3 and parts[1] == "modules":
                        imported_module = parts[2]
                        if imported_module != module_name:
                            violations.append(
                                f"{module_name}/infrastructure/{file_path.name}: "
                                f"imports '{imp}' (cross-module infrastructure)"
                            )

        assert not violations, (
            "Infrastructure layer MUST NOT import from other modules' infrastructure.\n"
            "Shared infrastructure should be in shared/infrastructure/.\n"
            "Exception: ORM model files (*_model.py) for FK relationships.\n"
            f"Found {len(violations)} violation(s):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestModulePublicApiExports:
    """Test that modules properly define their public API in __init__.py."""

    @pytest.fixture
    def backend_src_path(self) -> Path:
        """Get the backend src path."""
        current = Path(__file__).parent
        return current.parent.parent / "src"

    def test_modules_have_init_with_all(self, backend_src_path: Path):
        """Each module should have __init__.py with __all__ defined.

        This ensures explicit public API definition.
        """
        modules_path = backend_src_path / "modules"
        violations = []

        for module_dir in modules_path.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith("_"):
                init_file = module_dir / "__init__.py"
                if not init_file.exists():
                    violations.append(f"{module_dir.name}: missing __init__.py")
                    continue

                content = init_file.read_text()
                if "__all__" not in content:
                    violations.append(
                        f"{module_dir.name}: __init__.py missing __all__ definition"
                    )

        # This is a soft check - warn but don't fail
        if violations:
            import warnings
            warnings.warn(
                "Some modules are missing proper __init__.py or __all__ exports:\n"
                + "\n".join(f"  - {v}" for v in violations)
            )
