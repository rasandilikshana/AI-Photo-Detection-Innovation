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
