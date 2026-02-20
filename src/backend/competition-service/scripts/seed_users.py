"""
Seed script to create admin and judge users

Run from the competition-service directory:
    cd src/backend/competition-service
    python -m scripts.seed_users

Or with environment setup:
    source venv/bin/activate
    python -m scripts.seed_users
"""

import asyncio
import sys
import os

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models.user import User, UserRole
from app.utils.auth import get_password_hash


# Default users to seed
SEED_USERS = [
    {
        "email": "admin@avar.com",
        "username": "admin",
        "password": "Admin@123!",
        "full_name": "System Administrator",
        "role": UserRole.ADMIN,
        "is_active": True,
        "is_verified": True,
    },
    {
        "email": "judge@avar.com",
        "username": "judge",
        "password": "Judge@123!",
        "full_name": "Competition Judge",
        "role": UserRole.JUDGE,
        "is_active": True,
        "is_verified": True,
    },
    {
        "email": "organizer@avar.com",
        "username": "organizer",
        "password": "Organizer@123!",
        "full_name": "Competition Organizer",
        "role": UserRole.ORGANIZER,
        "is_active": True,
        "is_verified": True,
    },
]


async def seed_users():
    """Create seed users if they don't exist"""
    print("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as db:
        for user_data in SEED_USERS:
            # Check if user already exists
            result = await db.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"User '{user_data['username']}' already exists, updating role to {user_data['role'].value}...")
                existing.role = user_data["role"]
                existing.is_active = user_data["is_active"]
                existing.is_verified = user_data["is_verified"]
            else:
                print(f"Creating user '{user_data['username']}' with role {user_data['role'].value}...")
                new_user = User(
                    email=user_data["email"],
                    username=user_data["username"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    is_active=user_data["is_active"],
                    is_verified=user_data["is_verified"],
                )
                db.add(new_user)

        await db.commit()
        print("\nSeed users created/updated successfully!")
        print("\n" + "="*60)
        print("LOGIN CREDENTIALS:")
        print("="*60)
        for user_data in SEED_USERS:
            print(f"\n{user_data['role'].value.upper()}:")
            print(f"  Email:    {user_data['email']}")
            print(f"  Password: {user_data['password']}")
        print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(seed_users())
