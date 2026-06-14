"""Seed initial data for development."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.config.settings import get_settings


async def seed_admin_user(session: AsyncSession) -> None:
    """Create admin user if not exists."""
    # Check if admin exists
    result = await session.execute(text("SELECT id FROM users WHERE username = 'admin'"))
    if result.scalar_one_or_none():
        print("Admin user already exists")
        return

    # Create admin user
    # status/role/auth_type 使用小写 enum .value，与 ORM lowercase_enum 列对齐；
    # 切勿写大写(如 'ACTIVE')，否则读回会抛 LookupError 导致登录 500。
    password_hash = bcrypt.hashpw(b"Admin123!", bcrypt.gensalt()).decode()
    await session.execute(
        text("""
            INSERT INTO users (username, email, password_hash, status, role, auth_type, created_at, updated_at)
            VALUES ('admin', 'admin@example.com', :password_hash, 'active', 'admin', 'local', NOW(), NOW())
        """),
        {"password_hash": password_hash},
    )
    await session.commit()
    print("Admin user created: admin / Admin123!")


async def seed_resource_quotas(session: AsyncSession) -> None:
    """Create sample resource quotas."""
    result = await session.execute(text("SELECT COUNT(*) FROM resource_quotas"))
    if result.scalar_one() > 0:
        print("Resource quotas already exist")
        return

    # Get admin user id
    result = await session.execute(text("SELECT id FROM users WHERE username = 'admin'"))
    admin_id = result.scalar_one_or_none()

    await session.execute(
        text("""
            INSERT INTO resource_quotas (
                name, description, quota_type,
                max_cpu_cores, reserved_cpu_cores,
                max_gpu_count, reserved_gpu_count,
                max_memory_gb, reserved_memory_gb,
                max_storage_gb, max_concurrent_jobs, max_spot_instances,
                status, created_by, created_at, updated_at
            ) VALUES (
                'default-quota', 'Default resource quota for development',
                'user', 32, 0, 8, 0, 128, 0, 1000, 5, 2,
                'active', :created_by, NOW(), NOW()
            )
        """),
        {"created_by": admin_id},
    )
    await session.commit()
    print("Default resource quota created")


async def main() -> None:
    """Run seed script."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await seed_admin_user(session)
        await seed_resource_quotas(session)

    await engine.dispose()
    print("Seed completed!")


if __name__ == "__main__":
    asyncio.run(main())
