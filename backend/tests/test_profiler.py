import pytest
from backend.app.engine.profiler import DataProfiler
from backend.app.engine.expectations import ExpectationsEngine

def test_infer_type():
    assert DataProfiler.infer_type([1, 2, 3, 4]) == "INTEGER"
    assert DataProfiler.infer_type([1.5, 2.7, 3.0]) == "FLOAT"
    assert DataProfiler.infer_type([True, False, True]) == "BOOLEAN"
    assert DataProfiler.infer_type(["2026-01-01", "2026-01-02"]) == "DATETIME"
    assert DataProfiler.infer_type(["alpha", "beta", "gamma"]) == "STRING"

def test_profile_column_numeric():
    vals = [10, 20, 30, 40, 50, 500] # 500 is outlier
    res = DataProfiler.profile_column("test_num", vals)
    assert res["inferred_type"] == "INTEGER"
    assert res["null_count"] == 0
    assert res["completeness_pct"] == 100.0
    assert res["min_val"] == "10.0"
    assert res["max_val"] == "500.0"
    assert res["outliers_count"] >= 1

def test_assertions_evaluation():
    records = [
        {"id": 1, "score": 90},
        {"id": 2, "score": 85},
        {"id": 3, "score": None}
    ]
    rules = [
        {"assertion_type": "expect_column_values_to_not_be_null", "column_name": "id"},
        {"assertion_type": "expect_column_values_to_not_be_null", "column_name": "score"}
    ]
    results, health_score = ExpectationsEngine.evaluate_assertions(records, rules)
    assert len(results) == 2
    assert results[0]["passed"] is True
    assert results[1]["passed"] is False
    assert health_score == 50.0

def test_detect_schema_drift():
    baseline = {"id": "INTEGER", "name": "STRING", "created_at": "DATETIME"}
    current_drifted = {"id": "INTEGER", "name": "STRING", "extra_col": "FLOAT"}
    drift = ExpectationsEngine.detect_schema_drift(baseline, current_drifted)
    assert drift["has_drift"] is True
    assert "created_at" in drift["missing_columns"]
    assert "extra_col" in drift["unexpected_columns"]
