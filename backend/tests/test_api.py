import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_healthcheck():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "DataQualityX"

def test_stats_endpoint():
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "totalDatasets" in data
    assert "averageHealthScore" in data

def test_profile_and_save_dataset():
    payload = {
        "name": "Production User Stream",
        "description": "Daily customer feed"
    }
    res = client.post("/api/datasets", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Production User Stream"
    assert data["row_count"] == 8
    assert len(data["profiles"]) >= 5
    assert "health_score" in data

    # Detail check
    ds_id = data["id"]
    detail_res = client.get(f"/api/datasets/{ds_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == ds_id
    assert len(detail["profiles"]) >= 5

def test_schema_drift_endpoint():
    payload = {
        "dataset_name": "Production User Stream",
        "current_schema": {
            "user_id": "INTEGER",
            "email": "STRING",
            "age": "INTEGER",
            "country": "STRING",
            "amount": "FLOAT",
            "status": "STRING",
            "new_feature": "BOOLEAN"
        }
    }
    res = client.post("/api/schema/drift", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["has_drift"] is True
    assert "new_feature" in data["unexpected_columns"]
