"""
Creates the first admin user. Run once after the database is up:

    docker compose exec api python scripts/seed_admin.py

Reads credentials from env vars ADMIN_EMAIL / ADMIN_PASSWORD / ADMIN_NAME,
falling back to prompting interactively so a password never has to be
hardcoded anywhere.
"""
import asyncio
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select  # noqa: E402

from app.auth.security import hash_password  # noqa: E402
from app.database.session import AsyncSessionLocal, ensure_database_exists, init_models  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


async def main():
    ensure_database_exists()
    await init_models()

    email = os.getenv("ADMIN_EMAIL") or input("Admin email: ").strip()
    full_name = os.getenv("ADMIN_NAME") or input("Admin full name: ").strip()
    password = os.getenv("ADMIN_PASSWORD") or getpass.getpass("Admin password (min 8 chars): ")

    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"User {email} already exists.")
            return

        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role=UserRole.admin,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        print(f"Admin user created: {email}")


if __name__ == "__main__":
    asyncio.run(main())
