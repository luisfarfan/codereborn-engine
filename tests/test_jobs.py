"""
Integration tests for the Jobs router.

These tests exercise the full HTTP layer → service → DB path
using the in-memory SQLite test database.
"""

import pytest


@pytest.mark.asyncio
async def test_create_job_minimal(client):
    response = await client.post(
        "/api/v1/jobs",
        json={"repo_url": "https://github.com/example/repo", "analysis_scope": "quick"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["repo_url"] == "https://github.com/example/repo"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_job_with_budget(client):
    response = await client.post(
        "/api/v1/jobs",
        json={
            "repo_url": "https://github.com/example/repo",
            "analysis_scope": "standard",
            "budget": {"max_usd": 1.0, "mode": "balanced"},
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_job_missing_source(client):
    response = await client.post("/api/v1/jobs", json={"analysis_scope": "quick"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_jobs_empty(client):
    response = await client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_job_not_found(client):
    import uuid
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/jobs/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_job(client):
    create = await client.post(
        "/api/v1/jobs",
        json={"repo_url": "https://github.com/example/to-cancel", "analysis_scope": "quick"},
    )
    job_id = create.json()["id"]

    cancel = await client.delete(f"/api/v1/jobs/{job_id}", json={"reason": "test cancel"})
    assert cancel.status_code == 204

    get = await client.get(f"/api/v1/jobs/{job_id}")
    assert get.json()["status"] == "cancelled"
