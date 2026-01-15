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
