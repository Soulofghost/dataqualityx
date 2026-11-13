import re
import json
from typing import List, Dict, Any, Tuple

class ExpectationsEngine:
    @staticmethod
    def evaluate_assertions(records: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float]:
        """
        Evaluates assertions against tabular records.
        Returns list of test results and overall health score percentage.
        """
        results = []
        passed_count = 0

        for rule in rules:
            rule_type = rule.get("assertion_type")
            col = rule.get("column_name")
            params = rule.get("parameters", {})

            vals = [r.get(col) for r in records]
            passed = True
            msg = "Assertion passed."

            if rule_type == "expect_column_values_to_not_be_null":
                nulls = sum(1 for v in vals if v is None or v == "" or str(v).lower() in ["nan", "none", "null"])
                if nulls > 0:
                    passed = False
                    msg = f"Found {nulls} unexpected null values in column '{col}'."

            elif rule_type == "expect_column_values_to_be_unique":
                non_nulls = [v for v in vals if v is not None]
                if len(non_nulls) != len(set(non_nulls)):
                    passed = False
                    msg = f"Duplicate values detected in column '{col}' (Uniqueness violated)."

            elif rule_type == "expect_column_values_to_be_between":
                min_v = params.get("min")
                max_v = params.get("max")
                for v in vals:
                    if v is not None:
                        try:
                            f = float(v)
                            if (min_v is not None and f < min_v) or (max_v is not None and f > max_v):
                                passed = False
                                msg = f"Value {f} in '{col}' falls outside allowed range [{min_v}, {max_v}]."
                                break
                        except ValueError:
                            passed = False
                            msg = f"Non-numeric value '{v}' in range-checked column '{col}'."
                            break

            elif rule_type == "expect_column_values_to_match_regex":
                pattern = params.get("pattern", r".*")
                for v in vals:
                    if v is not None and not re.match(pattern, str(v)):
                        passed = False
                        msg = f"Value '{v}' does not match regex pattern '{pattern}'."
                        break

            if passed:
                passed_count += 1

            results.append({
                "assertion_type": rule_type,
                "column_name": col,
                "parameters": json.dumps(params),
                "passed": passed,
                "message": msg
            })

        total = len(rules) if rules else 1
        health_score = round((passed_count / total) * 100.0, 1) if rules else 100.0

        return results, health_score

    @staticmethod
    def detect_schema_drift(baseline_schema: Dict[str, str], current_schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Detects missing columns, unexpected columns, and type drift.
        """
        missing_columns = [col for col in baseline_schema if col not in current_schema]
        unexpected_columns = [col for col in current_schema if col not in baseline_schema]
        type_mismatches = []

        for col in baseline_schema:
            if col in current_schema:
                if baseline_schema[col] != current_schema[col]:
                    type_mismatches.append({
                        "column": col,
                        "expected_type": baseline_schema[col],
                        "actual_type": current_schema[col]
                    })

        has_drift = bool(missing_columns or unexpected_columns or type_mismatches)

        return {
            "has_drift": has_drift,
            "missing_columns": missing_columns,
            "unexpected_columns": unexpected_columns,
            "type_mismatches": type_mismatches
        }
