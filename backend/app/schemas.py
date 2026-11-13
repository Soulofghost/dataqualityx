from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AssertionRule(BaseModel):
    assertion_type: str = Field(..., description="expect_column_values_to_not_be_null, expect_column_values_to_be_unique, expect_column_values_to_be_between, expect_column_values_to_match_regex")
    column_name: str
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)

class UploadDatasetRequest(BaseModel):
    name: str = Field(..., description="Dataset name, e.g. Customer Ingestion Pipeline")
    description: Optional[str] = Field(default="")
    records: Optional[List[Dict[str, Any]]] = Field(default=None)
    assertions: Optional[List[AssertionRule]] = Field(default=None)

class ColumnProfileResponse(BaseModel):
    column_name: str
    inferred_type: str
    null_count: int
    completeness_pct: float
    distinct_count: int
    min_val: Optional[str]
    max_val: Optional[str]
    mean_val: Optional[float]
    outliers_count: int

class AssertionResultItem(BaseModel):
    assertion_type: str
    column_name: str
    parameters: str
    passed: bool
    message: str

class DatasetDetailResponse(BaseModel):
    id: str
    name: str
    description: str
    row_count: int
    column_count: int
    health_score: float
    created_at: str
    profiles: List[ColumnProfileResponse]
    assertions: List[AssertionResultItem]

class SchemaDriftRequest(BaseModel):
    dataset_name: str
    current_schema: Dict[str, str]

class SchemaDriftResponse(BaseModel):
    has_drift: bool
    missing_columns: List[str]
    unexpected_columns: List[str]
    type_mismatches: List[Dict[str, str]]
