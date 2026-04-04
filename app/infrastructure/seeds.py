"""
Seeding utilities for CodeReborn Engine.
Inserts initial fixed users for frontend development.
"""

import logging
import uuid
from sqlmodel import select
from app.infrastructure.database import AsyncSessionFactory
from app.models.db_models import User

logger = logging.getLogger(__name__)

# Fixed IDs for consistency during frontend dev
LUCHO_ID = uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
DEMO_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")

INITIAL_USERS = [
    {
        "id": LUCHO_ID,
        "email": "lucho@codereborn.io",
        "full_name": "Lucho Developer",
        "github_username": "lucho-dev",
        "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=lucho",
    },
    {
        "id": DEMO_ID,
        "email": "demo@codereborn.io",
        "full_name": "Demo User",
        "github_username": "demo-user",
        "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=demo",
    },
]


async def seed_initial_data():
    """Inserts initial users if they don't exist."""
    async with AsyncSessionFactory() as session:
        for user_data in INITIAL_USERS:
            # Check by email
            stmt = select(User).where(User.email == user_data["email"])
            result = await session.execute(stmt)
            existing = result.scalars().first()

            if not existing:
                user = User(**user_data)
                session.add(user)
                logger.info(f"Seeding user: {user.full_name}")
            else:
                # Update existing (if we changed avatar etc in code)
                for key, value in user_data.items():
                    setattr(existing, key, value)
                
        await session.commit()
    logger.info("✅ Database seeding completed")
