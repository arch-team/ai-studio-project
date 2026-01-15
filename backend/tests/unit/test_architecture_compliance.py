"""Architecture compliance tests - Verify Clean Architecture dependency rules.

This test ensures that the application layer does not directly import
infrastructure layer modules, maintaining proper dependency direction:
    API → Application → Domain ← Infrastructure
"""

import ast
import os
from pathlib import Path

import pytest


def get_python_files(directory: Path) -> list[Path]:
    """Get all Python files in directory recursively."""
    return list(directory.rglob("*.py"))


def get_imports_from_file(file_path: Path) -> list[str]:
    """Extract all import statements from a Python file."""
    imports = []
    try:
        with open(file_path, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
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
