import math
import re
from typing import List, Dict, Any, Optional

class DataProfiler:
    @staticmethod
    def infer_type(values: List[Any]) -> str:
        non_nulls = [v for v in values if v is not None and v != ""]
        if not non_nulls:
            return "UNKNOWN"

        is_bool = all(isinstance(v, bool) or str(v).lower() in ["true", "false"] for v in non_nulls)
        if is_bool: return "BOOLEAN"

        is_int = True
        for v in non_nulls:
            try:
                int_val = int(v)
                if float(v) != int_val:
                    is_int = False
                    break
            except (ValueError, TypeError):
                is_int = False
                break
        if is_int: return "INTEGER"

        is_float = True
        for v in non_nulls:
            try:
                float(v)
            except (ValueError, TypeError):
                is_float = False
                break
        if is_float: return "FLOAT"

        # Check date ISO
        is_date = all(bool(re.match(r'^\d{4}-\d{2}-\d{2}', str(v))) for v in non_nulls)
        if is_date: return "DATETIME"

        return "STRING"

    @staticmethod
    def profile_column(col_name: str, values: List[Any]) -> Dict[str, Any]:
        total_rows = len(values)
        null_count = sum(1 for v in values if v is None or v == "" or str(v).lower() in ["nan", "none", "null"])
        completeness_pct = round(((total_rows - null_count) / total_rows * 100.0), 2) if total_rows > 0 else 0.0

        inferred_type = DataProfiler.infer_type(values)
        non_nulls = [v for v in values if v is not None and v != "" and str(v).lower() not in ["nan", "none", "null"]]
        distinct_count = len(set(non_nulls))

        min_val = None
        max_val = None
        mean_val = None
        outliers_count = 0

        if inferred_type in ["INTEGER", "FLOAT"] and non_nulls:
            numeric_vals = sorted([float(v) for v in non_nulls])
            min_val = str(numeric_vals[0])
            max_val = str(numeric_vals[-1])
            mean_val = round(sum(numeric_vals) / len(numeric_vals), 2)

            # Calculate IQR Outliers
            n = len(numeric_vals)
            q1 = numeric_vals[int(n * 0.25)]
            q3 = numeric_vals[int(n * 0.75)]
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers_count = sum(1 for v in numeric_vals if v < lower_bound or v > upper_bound)
        elif non_nulls:
            min_val = str(min(non_nulls, key=lambda x: str(x)))
            max_val = str(max(non_nulls, key=lambda x: str(x)))

        return {
            "column_name": col_name,
            "inferred_type": inferred_type,
            "null_count": null_count,
            "completeness_pct": completeness_pct,
            "distinct_count": distinct_count,
            "min_val": min_val,
            "max_val": max_val,
            "mean_val": mean_val,
            "outliers_count": outliers_count
        }

    @staticmethod
    def profile_dataset(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not records:
            return {"row_count": 0, "column_count": 0, "columns": []}

        columns = list(records[0].keys())
        col_profiles = []

        for col in columns:
            vals = [r.get(col) for r in records]
            col_profiles.append(DataProfiler.profile_column(col, vals))

        return {
            "row_count": len(records),
            "column_count": len(columns),
            "columns": col_profiles
        }
