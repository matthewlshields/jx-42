from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, cast

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"


def load_schema(name: str) -> Dict[str, Any]:
    path = SCHEMA_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        return cast(Dict[str, Any], json.load(handle))


def validate_required_fields(payload: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required = schema.get("required", [])
    for field in required:
        if field not in payload:
            errors.append(f"Missing required field: {field}")
    properties = schema.get("properties", {})
    for field, rules in properties.items():
        if field not in payload:
            continue
        value = payload[field]
        expected_type = rules.get("type")
        if expected_type and not _matches_type(value, expected_type):
            errors.append(f"Field {field} expected {expected_type}")
        if "enum" in rules and value not in rules["enum"]:
            errors.append(f"Field {field} must be one of {rules['enum']}")

        # Enforce basic numeric constraints if defined in the schema.
        # This aligns with JSON Schema's "minimum" and "maximum" keywords.
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            minimum = rules.get("minimum")
            maximum = rules.get("maximum")
            if minimum is not None and value < minimum:
                errors.append(f"Field {field} must be >= {minimum}")
            if maximum is not None and value > maximum:
                errors.append(f"Field {field} must be <= {maximum}")
    return errors


def validate_audit_event(payload: Dict[str, Any]) -> List[str]:
    schema = load_schema("audit_event.schema.json")
    return validate_required_fields(payload, schema)


def validate_finance_ledger_entry(payload: Dict[str, Any]) -> List[str]:
    schema = load_schema("finance_ledger.schema.json")
    return validate_required_fields(payload, schema)


def validate_investing_trade_ticket(payload: Dict[str, Any]) -> List[str]:
    schema = load_schema("investing_trade_ticket.schema.json")
    return validate_required_fields(payload, schema)


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "boolean":
        return isinstance(value, bool)
    return True
