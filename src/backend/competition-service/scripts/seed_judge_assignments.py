"""
Seed script to create judge assignments for existing competitions

Run from the competition-service directory:
    cd src/backend/competition-service
    source venv/bin/activate
    python -m scripts.seed_judge_assignments
"""

import asyncio
import sys
import os

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models.user import User, UserRole
from app.models.competition import Competition
from app.models.judge import JudgeAssignment


async def seed_judge_assignments():
    """Assign judges to all open/judging competitions"""
    print("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # Get all judges
        result = await db.execute(
            select(User).where(User.role == UserRole.JUDGE)
        )
        judges = result.scalars().all()

        if not judges:
            print("ERROR: No judges found. Please run seed_users.py first.")
            return

        print(f"Found {len(judges)} judges:")
        for judge in judges:
            print(f"  - {judge.username} (ID: {judge.id})")

        # Get all competitions (except draft and cancelled)
        result = await db.execute(
            select(Competition).where(
                Competition.status.notin_(["draft", "cancelled"])
            )
        )
        competitions = result.scalars().all()

        if not competitions:
            print("ERROR: No competitions found. Please run seed_competitions.py first.")
            return

        print(f"\nFound {len(competitions)} competitions:")
        for comp in competitions:
            print(f"  - {comp.title} (Status: {comp.status.value})")

        # Assign each judge to each competition
        assignments_created = 0
        for judge in judges:
            for comp in competitions:
                # Check if assignment already exists
                result = await db.execute(
                    select(JudgeAssignment).where(
                        JudgeAssignment.judge_id == judge.id,
                        JudgeAssignment.competition_id == comp.id,
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    print(f"Assignment already exists: {judge.username} -> {comp.title}")
                    continue

                assignment = JudgeAssignment(
                    judge_id=judge.id,
                    competition_id=comp.id,
                    is_active=True,
                )
                db.add(assignment)
                assignments_created += 1
                print(f"Created assignment: {judge.username} -> {comp.title}")

        await db.commit()

        print("\n" + "=" * 60)
        print(f"Judge assignments created: {assignments_created}")
        print("=" * 60)
        print("\nJudges can now access the Judge Dashboard to score submissions.")
        print("Login as judge@avar.com / Judge@123!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_judge_assignments())
