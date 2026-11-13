import uuid
import datetime
import json
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from backend.app.database import get_connection
from backend.app.schemas import (
    UploadDatasetRequest, DatasetDetailResponse,
    SchemaDriftRequest, SchemaDriftResponse
)
from backend.app.engine.profiler import DataProfiler
from backend.app.engine.expectations import ExpectationsEngine

router = APIRouter(prefix="/api", tags=["quality"])

@router.get("/health")
def healthcheck():
    return {
        "status": "ok",
        "service": "DataQualityX",
        "version": "1.0.0",
        "engine": "Automated Column Profiler, Data Assertions & Schema Drift Sentinel"
    }

@router.get("/stats")
def get_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as c FROM datasets;")
    total_datasets = cursor.fetchone()["c"]

    cursor.execute("SELECT AVG(health_score) as a FROM datasets;")
    avg_score_row = cursor.fetchone()["a"]
    avg_health_score = round(avg_score_row, 1) if avg_score_row else 100.0

    cursor.execute("SELECT COUNT(*) as c FROM column_profiles WHERE outliers_count > 0;")
    columns_with_outliers = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(*) as c FROM quality_assertions WHERE passed = 0;")
    failed_assertions = cursor.fetchone()["c"]

    conn.close()

    return {
        "totalDatasets": total_datasets,
        "averageHealthScore": avg_health_score,
        "columnsWithOutliers": columns_with_outliers,
        "failedAssertionsCount": failed_assertions
    }

@router.get("/datasets")
def list_datasets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets ORDER BY created_at DESC;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/datasets", response_model=DatasetDetailResponse, status_code=status.HTTP_201_CREATED)
def profile_and_save_dataset(payload: UploadDatasetRequest):
    records = payload.records
    if not records:
        # Seed realistic enterprise e-commerce customer transaction records
        records = [
            {"user_id": 101, "email": "alice@corp.com", "age": 29, "country": "US", "amount": 149.99, "status": "COMPLETED"},
            {"user_id": 102, "email": "bob@corp.com", "age": 42, "country": "UK", "amount": 320.00, "status": "COMPLETED"},
            {"user_id": 103, "email": "carol@corp.com", "age": 35, "country": "DE", "amount": 89.50, "status": "PENDING"},
            {"user_id": 104, "email": "dan@corp.com", "age": 58, "country": "FR", "amount": 450.00, "status": "COMPLETED"},
            {"user_id": 105, "email": "eve@corp.com", "age": 24, "country": "US", "amount": 12.00, "status": "REFUNDED"},
            {"user_id": 106, "email": "frank@corp.com", "age": 31, "country": "CA", "amount": 9999.00, "status": "COMPLETED"}, # Outlier
            {"user_id": 107, "email": "grace@corp.com", "age": None, "country": "US", "amount": 75.00, "status": "COMPLETED"}, # Null age
            {"user_id": 108, "email": "heidi@corp.com", "age": 47, "country": "US", "amount": 210.00, "status": "COMPLETED"}
        ]

    # Run profiling
    profile_summary = DataProfiler.profile_dataset(records)

    # Run assertions
    rules = []
    if payload.assertions:
        rules = [a.model_dump() for a in payload.assertions]
    else:
        # Default expectations
        rules = [
            {"assertion_type": "expect_column_values_to_not_be_null", "column_name": "user_id"},
            {"assertion_type": "expect_column_values_to_be_unique", "column_name": "user_id"},
            {"assertion_type": "expect_column_values_to_not_be_null", "column_name": "email"},
            {"assertion_type": "expect_column_values_to_be_between", "column_name": "amount", "parameters": {"min": 0.0, "max": 5000.0}}, # Will fail on 9999
            {"assertion_type": "expect_column_values_to_not_be_null", "column_name": "age"} # Will fail on 107
        ]

    assertion_results, health_score = ExpectationsEngine.evaluate_assertions(records, rules)

    dataset_id = "dset-" + str(uuid.uuid4())[:8]
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO datasets (id, name, description, row_count, column_count, health_score, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (dataset_id, payload.name, payload.description or "", profile_summary["row_count"], profile_summary["column_count"], health_score, now_iso))

    for p in profile_summary["columns"]:
        col_id = "col-" + str(uuid.uuid4())[:8]
        cursor.execute("""
        INSERT INTO column_profiles (id, dataset_id, column_name, inferred_type, null_count, completeness_pct, distinct_count, min_val, max_val, mean_val, outliers_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (col_id, dataset_id, p["column_name"], p["inferred_type"], p["null_count"], p["completeness_pct"], p["distinct_count"], p["min_val"], p["max_val"], p["mean_val"], p["outliers_count"]))

    for a in assertion_results:
        ast_id = "ast-" + str(uuid.uuid4())[:8]
        cursor.execute("""
        INSERT INTO quality_assertions (id, dataset_id, assertion_type, column_name, parameters, passed, message)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (ast_id, dataset_id, a["assertion_type"], a["column_name"], a["parameters"], 1 if a["passed"] else 0, a["message"]))

    # Update or save baseline schema
    current_schema = {p["column_name"]: p["inferred_type"] for p in profile_summary["columns"]}
    cursor.execute("""
    INSERT INTO schema_baselines (id, dataset_name, schema_json, updated_at)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(dataset_name) DO UPDATE SET schema_json = excluded.schema_json, updated_at = excluded.updated_at;
    """, (str(uuid.uuid4()), payload.name, json.dumps(current_schema), now_iso))

    conn.commit()
    conn.close()

    return {
        "id": dataset_id,
        "name": payload.name,
        "description": payload.description or "",
        "row_count": profile_summary["row_count"],
        "column_count": profile_summary["column_count"],
        "health_score": health_score,
        "created_at": now_iso,
        "profiles": profile_summary["columns"],
        "assertions": assertion_results
    }

@router.get("/datasets/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset_detail(dataset_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM datasets WHERE id = ?;", (dataset_id,))
    ds_row = cursor.fetchone()
    if not ds_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Dataset not found")

    cursor.execute("SELECT * FROM column_profiles WHERE dataset_id = ? ORDER BY column_name ASC;", (dataset_id,))
    profiles = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM quality_assertions WHERE dataset_id = ?;", (dataset_id,))
    assertions = [
        {
            **dict(r),
            "passed": bool(r["passed"])
        } for r in cursor.fetchall()
    ]

    conn.close()

    return {
        **dict(ds_row),
        "profiles": profiles,
        "assertions": assertions
    }

@router.post("/schema/drift", response_model=SchemaDriftResponse)
def evaluate_drift(payload: SchemaDriftRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT schema_json FROM schema_baselines WHERE dataset_name = ?;", (payload.dataset_name,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        # If no baseline registered, create baseline from current schema
        return {
            "has_drift": False,
            "missing_columns": [],
            "unexpected_columns": [],
            "type_mismatches": []
        }

    baseline_schema = json.loads(row["schema_json"])
    drift_result = ExpectationsEngine.detect_schema_drift(baseline_schema, payload.current_schema)

    return drift_result
