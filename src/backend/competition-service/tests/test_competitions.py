"""
Tests for competition management endpoints
"""

import pytest
from httpx import AsyncClient
from app.models.user import UserRole


@pytest.mark.asyncio
async def test_create_competition_as_organizer(
    client: AsyncClient, authenticated_user: dict, test_competition_data: dict, db
):
    """Test creating competition as organizer"""
    # Update user role to organizer
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == authenticated_user["user"]["email"]))
    user = result.scalar_one()
    user.role = UserRole.ORGANIZER
    await db.commit()

    # Create competition
    response = await client.post(
        "/api/v1/competitions",
        json=test_competition_data,
        headers=authenticated_user["headers"],
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == test_competition_data["title"]
    assert data["slug"] is not None
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_create_competition_as_participant(
    client: AsyncClient, authenticated_user: dict, test_competition_data: dict
):
    """Test that participants cannot create competitions"""
    response = await client.post(
        "/api/v1/competitions",
        json=test_competition_data,
        headers=authenticated_user["headers"],
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_competitions(
    client: AsyncClient, authenticated_user: dict, test_competition_data: dict, db
):
    """Test listing competitions"""
    # Update user to organizer and create a competition
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == authenticated_user["user"]["email"]))
    user = result.scalar_one()
    user.role = UserRole.ORGANIZER
    await db.commit()

    await client.post(
        "/api/v1/competitions",
        json=test_competition_data,
        headers=authenticated_user["headers"],
    )

    # List competitions
    response = await client.get("/api/v1/competitions")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["title"] == test_competition_data["title"]


@pytest.mark.asyncio
async def test_get_competition_by_id(
    client: AsyncClient, authenticated_user: dict, test_competition_data: dict, db
):
    """Test getting competition by ID"""
    # Update user to organizer and create a competition
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == authenticated_user["user"]["email"]))
    user = result.scalar_one()
    user.role = UserRole.ORGANIZER
    await db.commit()

    create_response = await client.post(
        "/api/v1/competitions",
        json=test_competition_data,
        headers=authenticated_user["headers"],
    )
    competition_id = create_response.json()["id"]

    # Get competition
    response = await client.get(f"/api/v1/competitions/{competition_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == competition_id
    assert data["title"] == test_competition_data["title"]


@pytest.mark.asyncio
async def test_get_competition_by_slug(
    client: AsyncClient, authenticated_user: dict, test_competition_data: dict, db
):
    """Test getting competition by slug"""
    # Update user to organizer and create a competition
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == authenticated_user["user"]["email"]))
    user = result.scalar_one()
    user.role = UserRole.ORGANIZER
    await db.commit()

    create_response = await client.post(
        "/api/v1/competitions",
        json=test_competition_data,
        headers=authenticated_user["headers"],
    )
    slug = create_response.json()["slug"]

    # Get competition by slug
    response = await client.get(f"/api/v1/competitions/slug/{slug}")

    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == slug
    assert data["title"] == test_competition_data["title"]


@pytest.mark.asyncio
async def test_update_competition(
    client: AsyncClient, authenticated_user: dict, test_competition_data: dict, db
):
    """Test updating competition"""
    # Update user to organizer and create a competition
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == authenticated_user["user"]["email"]))
    user = result.scalar_one()
    user.role = UserRole.ORGANIZER
    await db.commit()

    create_response = await client.post(
        "/api/v1/competitions",
        json=test_competition_data,
        headers=authenticated_user["headers"],
    )
    competition_id = create_response.json()["id"]

    # Update competition
    update_data = {"title": "Updated Competition Title"}
    response = await client.patch(
        f"/api/v1/competitions/{competition_id}",
        json=update_data,
        headers=authenticated_user["headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]


@pytest.mark.asyncio
async def test_update_competition_settings(
    client: AsyncClient, authenticated_user: dict, test_competition_data: dict, db
):
    """Test updating deadline, max submissions, and other settings"""
    from datetime import datetime, timedelta
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == authenticated_user["user"]["email"]))
    user = result.scalar_one()
    user.role = UserRole.ORGANIZER
    await db.commit()

    create_response = await client.post(
        "/api/v1/competitions",
        json=test_competition_data,
        headers=authenticated_user["headers"],
    )
    competition_id = create_response.json()["id"]

    # Extend deadline and change settings
    new_end = (datetime.utcnow() + timedelta(days=60)).isoformat()
    update_data = {
        "submission_end": new_end,
        "max_submissions_per_user": 10,
        "prize_amount": 250000,
        "prize_description": "Grand prize: $2500",
        "require_raw_files": False,
        "allow_ai_generated": True,
        "entry_fee": 500,
    }
    response = await client.patch(
        f"/api/v1/competitions/{competition_id}",
        json=update_data,
        headers=authenticated_user["headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["submission_end"][:19] == new_end[:19]
    assert data["max_submissions_per_user"] == 10
    assert data["prize_amount"] == 250000
    assert data["prize_description"] == "Grand prize: $2500"
    assert data["require_raw_files"] is False
    assert data["allow_ai_generated"] is True
    assert data["entry_fee"] == 500


def test_schemas_normalize_timezone_aware_datetimes():
    """Browser clients send ISO dates with 'Z' — schemas must yield naive UTC datetimes
    because the DB columns are TIMESTAMP WITHOUT TIME ZONE (asyncpg rejects aware values)"""
    from app.schemas import CompetitionCreate, CompetitionUpdate

    update = CompetitionUpdate(
        submission_start="2026-02-20T17:47:00.000Z",
        submission_end="2027-03-22T17:47:00.000Z",
    )
    assert update.submission_start.tzinfo is None
    assert update.submission_end.tzinfo is None
    assert update.submission_end.isoformat() == "2027-03-22T17:47:00"

    create = CompetitionCreate(
        title="TZ Normalization Test",
        description="Ensures aware datetimes are converted to naive UTC",
        submission_start="2026-02-20T17:47:00.000Z",
        submission_end="2027-03-22T23:47:00.000+06:00",  # naive UTC: 17:47
    )
    assert create.submission_start.tzinfo is None
    assert create.submission_end.tzinfo is None
    assert create.submission_end.isoformat() == "2027-03-22T17:47:00"


@pytest.mark.asyncio
async def test_update_competition_with_utc_z_dates(
    client: AsyncClient, authenticated_user: dict, test_competition_data: dict, db
):
    """Regression: PATCH with browser-style 'Z' ISO dates must persist as naive UTC"""
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == authenticated_user["user"]["email"]))
    user = result.scalar_one()
    user.role = UserRole.ORGANIZER
    await db.commit()

    create_response = await client.post(
        "/api/v1/competitions",
        json=test_competition_data,
        headers=authenticated_user["headers"],
    )
    competition_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/competitions/{competition_id}",
        json={
            "submission_start": "2026-02-20T17:47:00.000Z",
            "submission_end": "2027-03-22T17:47:00.000Z",
            "max_submissions_per_user": 20,
        },
        headers=authenticated_user["headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["submission_end"] == "2027-03-22T17:47:00"
    assert "+00:00" not in data["submission_start"]
    assert data["max_submissions_per_user"] == 20


@pytest.mark.asyncio
async def test_update_competition_invalid_dates(
    client: AsyncClient, authenticated_user: dict, test_competition_data: dict, db
):
    """Test that submission_end before submission_start is rejected"""
    from datetime import datetime, timedelta
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == authenticated_user["user"]["email"]))
    user = result.scalar_one()
    user.role = UserRole.ORGANIZER
    await db.commit()

    create_response = await client.post(
        "/api/v1/competitions",
        json=test_competition_data,
        headers=authenticated_user["headers"],
    )
    competition_id = create_response.json()["id"]

    # submission_end before the existing submission_start (start is now + 1 day)
    update_data = {"submission_end": (datetime.utcnow() - timedelta(days=5)).isoformat()}
    response = await client.patch(
        f"/api/v1/competitions/{competition_id}",
        json=update_data,
        headers=authenticated_user["headers"],
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_competition_invalid_max_submissions(
    client: AsyncClient, authenticated_user: dict, test_competition_data: dict, db
):
    """Test that out-of-range max_submissions_per_user is rejected"""
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == authenticated_user["user"]["email"]))
    user = result.scalar_one()
    user.role = UserRole.ORGANIZER
    await db.commit()

    create_response = await client.post(
        "/api/v1/competitions",
        json=test_competition_data,
        headers=authenticated_user["headers"],
    )
    competition_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/competitions/{competition_id}",
        json={"max_submissions_per_user": 0},
        headers=authenticated_user["headers"],
    )
    assert response.status_code == 422

    response = await client.patch(
        f"/api/v1/competitions/{competition_id}",
        json={"max_submissions_per_user": 50},
        headers=authenticated_user["headers"],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_competition_non_owner_forbidden(
    client: AsyncClient, authenticated_user: dict, test_competition_data: dict, db
):
    """Test that a different user cannot update someone else's competition"""
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == authenticated_user["user"]["email"]))
    user = result.scalar_one()
    user.role = UserRole.ORGANIZER
    await db.commit()

    create_response = await client.post(
        "/api/v1/competitions",
        json=test_competition_data,
        headers=authenticated_user["headers"],
    )
    competition_id = create_response.json()["id"]

    # Register and login a second (participant) user
    other_user_data = {
        "email": "other@example.com",
        "username": "otheruser",
        "password": "OtherPassword123!",
        "full_name": "Other User",
    }
    response = await client.post("/api/v1/auth/register", json=other_user_data)
    assert response.status_code == 201
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": other_user_data["email"], "password": other_user_data["password"]},
    )
    assert response.status_code == 200
    other_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    response = await client.patch(
        f"/api/v1/competitions/{competition_id}",
        json={"max_submissions_per_user": 10},
        headers=other_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_competition(
    client: AsyncClient, authenticated_user: dict, test_competition_data: dict, db
):
    """Test deleting competition"""
    # Update user to organizer and create a competition
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.email == authenticated_user["user"]["email"]))
    user = result.scalar_one()
    user.role = UserRole.ORGANIZER
    await db.commit()

    create_response = await client.post(
        "/api/v1/competitions",
        json=test_competition_data,
        headers=authenticated_user["headers"],
    )
    competition_id = create_response.json()["id"]

    # Delete competition
    response = await client.delete(
        f"/api/v1/competitions/{competition_id}",
        headers=authenticated_user["headers"],
    )

    assert response.status_code == 200

    # Verify deletion
    get_response = await client.get(f"/api/v1/competitions/{competition_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_competition(client: AsyncClient):
    """Test getting non-existent competition"""
    response = await client.get("/api/v1/competitions/99999")

    assert response.status_code == 404
