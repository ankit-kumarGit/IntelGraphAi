import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import db_manager
from app.rag.vector_store import vector_store

@pytest.fixture(autouse=True)
def setup_test_env():
    db_manager.connect()
    vector_store.load()

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True

@pytest.mark.asyncio
async def test_overview_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/overview")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert data["metrics"]["total_assets"] >= 4

@pytest.mark.asyncio
async def test_asset_profile_and_knowledge_map():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res1 = await ac.get("/api/assets/P-101")
        res2 = await ac.get("/api/assets/P-101/knowledge-map")
    assert res1.status_code == 200
    assert res2.status_code == 200
    map_data = res2.json()
    assert len(map_data["nodes"]) >= 5
    assert len(map_data["links"]) >= 4

@pytest.mark.asyncio
async def test_grounded_chat_and_citations():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"query": "What is the maintenance history of P-101?", "asset_tag": "P-101"}
        res = await ac.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["refused"] is False
    assert len(data["citations"]) >= 1
    assert "bearing" in data["answer"].lower()

@pytest.mark.asyncio
async def test_idk_protection_unrecorded_query():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"query": "What is the calibration frequency of pressure transmitter X-99?", "asset_tag": "P-101"}
        res = await ac.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["refused"] is True
    assert "could not find sufficient information" in data["answer"].lower()

@pytest.mark.asyncio
async def test_rca_analysis():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/rca/analyze", data={"asset_tag": "P-101", "problem": "High Vibration"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["possible_causes"]) >= 2
    assert len(data["recommended_checks"]) >= 2
