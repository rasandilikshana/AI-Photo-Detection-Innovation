"""
Seed script to create sample competitions

Run from the competition-service directory:
    cd src/backend/competition-service
    source venv/bin/activate
    python -m scripts.seed_competitions
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models.user import User, UserRole
from app.models.competition import Competition, CompetitionStatus


# Sample competitions
SAMPLE_COMPETITIONS = [
    {
        "title": "Nature Photography Challenge 2024",
        "description": "Capture the beauty of nature in its purest form. We're looking for stunning landscapes, wildlife, and macro photography that showcases the natural world.",
        "rules": "1. Only original photographs taken by you\n2. Minimal post-processing allowed\n3. RAW files required\n4. No AI-generated or heavily manipulated images",
        "submission_start": datetime.utcnow() - timedelta(days=5),
        "submission_end": datetime.utcnow() + timedelta(days=25),
        "status": CompetitionStatus.OPEN,
        "max_submissions_per_user": 3,
        "require_raw_files": True,
        "allow_ai_generated": False,
        "prize_amount": 50000,  # $500 in cents
        "prize_description": "First place: $500, Second place: $250, Third place: $100",
    },
    {
        "title": "Urban Street Photography Contest",
        "description": "Show us the soul of the city through your lens. Capture candid moments, architecture, street life, and the unique character of urban environments.",
        "rules": "1. Street photography only - no studio shots\n2. Black & white or color accepted\n3. RAW files required\n4. Must be shot within the last year",
        "submission_start": datetime.utcnow() - timedelta(days=10),
        "submission_end": datetime.utcnow() + timedelta(days=20),
        "status": CompetitionStatus.OPEN,
        "max_submissions_per_user": 5,
        "require_raw_files": True,
        "allow_ai_generated": False,
        "prize_amount": 30000,  # $300 in cents
        "prize_description": "Winner takes all: $300 cash prize",
    },
    {
        "title": "Portrait Photography Excellence",
        "description": "Showcase your portrait photography skills. We want to see emotion, connection, and technical excellence in your portrait work.",
        "rules": "1. Studio or environmental portraits accepted\n2. Must have model release\n3. Basic retouching allowed\n4. RAW files required",
        "submission_start": datetime.utcnow() + timedelta(days=5),
        "submission_end": datetime.utcnow() + timedelta(days=35),
        "status": CompetitionStatus.OPEN,
        "max_submissions_per_user": 2,
        "require_raw_files": True,
        "allow_ai_generated": False,
        "prize_amount": 75000,  # $750 in cents
        "prize_description": "Grand prize: $750 + featured exhibition",
    },
    {
        "title": "Macro World Photography",
        "description": "Explore the tiny universe around us. Insects, flowers, textures, and anything that reveals hidden details invisible to the naked eye.",
        "rules": "1. True macro photography (1:1 or greater magnification)\n2. Focus stacking allowed\n3. Natural light preferred\n4. RAW files required",
        "submission_start": datetime.utcnow() - timedelta(days=30),
        "submission_end": datetime.utcnow() - timedelta(days=5),
        "status": CompetitionStatus.JUDGING,
        "max_submissions_per_user": 4,
        "require_raw_files": True,
        "allow_ai_generated": False,
        "prize_amount": 40000,  # $400 in cents
        "prize_description": "First: $400, Second: $200",
    },
    {
        "title": "PhotoTechno Competition 2026",
        "description": "The premier photography technology competition showcasing the intersection of traditional photography and cutting-edge techniques. Submit your best work demonstrating technical excellence and creative vision.",
        "rules": "1. All photographs must be original work\n2. RAW files are mandatory for verification\n3. Post-processing allowed but must maintain authenticity\n4. AI-generated images strictly prohibited\n5. Multiple camera formats accepted",
        "submission_start": datetime.utcnow(),
        "submission_end": datetime.utcnow() + timedelta(days=45),
        "status": CompetitionStatus.OPEN,
        "max_submissions_per_user": 5,
        "require_raw_files": True,
        "allow_ai_generated": False,
        "prize_amount": 100000,  # $1000 in cents
        "prize_description": "Grand Prize: $1000, Runner-up: $500, Third Place: $250",
    },
    {
        "title": "NPAS Monthly Competition - April 2026",
        "description": "NPAS's monthly photography competition for April 2026. Open to all skill levels. This month's theme: 'Moments in Time' - capture fleeting moments that tell a story.",
        "rules": "1. Theme: Moments in Time\n2. Original photographs only\n3. RAW file submission required\n4. Minimal post-processing encouraged\n5. No AI-generated content allowed",
        "submission_start": datetime.utcnow(),
        "submission_end": datetime.utcnow() + timedelta(days=30),
        "status": CompetitionStatus.OPEN,
        "max_submissions_per_user": 3,
        "require_raw_files": True,
        "allow_ai_generated": False,
        "prize_amount": 25000,  # $250 in cents
        "prize_description": "Winner: $250 + Featured in NPAS Gallery",
    },
]


async def seed_competitions():
    """Create sample competitions"""
    print("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # Get the organizer user (or admin as fallback)
        result = await db.execute(
            select(User).where(User.role == UserRole.ORGANIZER)
        )
        organizer = result.scalar_one_or_none()

        if not organizer:
            result = await db.execute(
                select(User).where(User.role == UserRole.ADMIN)
            )
            organizer = result.scalar_one_or_none()

        if not organizer:
            print("ERROR: No organizer or admin user found. Please run seed_users.py first.")
            return

        print(f"Using organizer: {organizer.username} (ID: {organizer.id})")

        for comp_data in SAMPLE_COMPETITIONS:
            # Check if competition already exists
            result = await db.execute(
                select(Competition).where(Competition.title == comp_data["title"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"Competition '{comp_data['title']}' already exists, skipping...")
                continue

            print(f"Creating competition: {comp_data['title']}...")

            # Create slug from title
            slug = comp_data["title"].lower().replace(" ", "-").replace("'", "")

            competition = Competition(
                title=comp_data["title"],
                description=comp_data["description"],
                rules=comp_data["rules"],
                slug=slug,
                submission_start=comp_data["submission_start"],
                submission_end=comp_data["submission_end"],
                status=comp_data["status"],
                max_submissions_per_user=comp_data["max_submissions_per_user"],
                require_raw_files=comp_data["require_raw_files"],
                allow_ai_generated=comp_data["allow_ai_generated"],
                prize_amount=comp_data["prize_amount"],
                prize_description=comp_data["prize_description"],
                entry_fee=0,
                organizer_id=organizer.id,
            )
            db.add(competition)

        await db.commit()
        print("\n" + "="*60)
        print("Sample competitions created successfully!")
        print("="*60)
        print(f"Total competitions: {len(SAMPLE_COMPETITIONS)}")
        print("\nYou can now view them at: http://localhost:5173/competitions")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(seed_competitions())
