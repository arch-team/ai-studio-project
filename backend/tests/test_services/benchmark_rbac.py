"""Benchmark RBAC Service performance."""

import time
from typing import Callable

from src.services.rbac_service import (
    Action,
    ResourceType,
    Role,
    RBACService,
)


def benchmark_function(func: Callable, iterations: int = 10000) -> float:
    """Benchmark a function."""
    start_time = time.perf_counter()
    for _ in range(iterations):
        func()
    end_time = time.perf_counter()
    return end_time - start_time


def run_benchmarks():
    """Run performance benchmarks."""
    service = RBACService()
    iterations = 10000

    print("RBAC Service Performance Benchmarks")
    print("=" * 50)
    print(f"Iterations: {iterations:,}")
    print("-" * 50)

    # Benchmark get_role_level
    time_valid = benchmark_function(
        lambda: service.get_role_level("admin"),
        iterations,
    )
    print(f"get_role_level (valid role):    {time_valid:.4f}s")

    time_invalid = benchmark_function(
        lambda: service.get_role_level("invalid"),
        iterations,
    )
    print(f"get_role_level (invalid role):  {time_invalid:.4f}s")

    # Benchmark has_minimum_role
    time_has_role = benchmark_function(
        lambda: service.has_minimum_role("engineer", Role.VIEWER),
        iterations,
    )
    print(f"has_minimum_role:                {time_has_role:.4f}s")

    # Benchmark check_permission
    time_check_basic = benchmark_function(
        lambda: service.check_permission(
            "engineer",
            ResourceType.TRAINING_JOB,
            Action.CREATE,
        ),
        iterations,
    )
    print(f"check_permission (basic):        {time_check_basic:.4f}s")

    time_check_owner = benchmark_function(
        lambda: service.check_permission(
            "engineer",
            ResourceType.TRAINING_JOB,
            Action.UPDATE,
            resource_owner_id=123,
            user_id=123,
        ),
        iterations,
    )
    print(f"check_permission (owner check):  {time_check_owner:.4f}s")

    # Benchmark get_allowed_actions
    time_actions = benchmark_function(
        lambda: service.get_allowed_actions(
            "engineer",
            ResourceType.TRAINING_JOB,
        ),
        iterations,
    )
    print(f"get_allowed_actions:             {time_actions:.4f}s")

    # Benchmark get_kubernetes_role_binding
    time_k8s = benchmark_function(
        lambda: service.get_kubernetes_role_binding("engineer", "namespace"),
        iterations,
    )
    print(f"get_kubernetes_role_binding:     {time_k8s:.4f}s")

    print("-" * 50)
    total_time = sum([
        time_valid,
        time_invalid,
        time_has_role,
        time_check_basic,
        time_check_owner,
        time_actions,
        time_k8s,
    ])
    print(f"Total time:                      {total_time:.4f}s")
    print(f"Average per operation:           {(total_time / (7 * iterations)) * 1000:.4f}ms")
    print("=" * 50)


if __name__ == "__main__":
    run_benchmarks()