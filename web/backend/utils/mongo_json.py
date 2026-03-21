"""
Convierte valores típicos de MongoDB a tipos serializables en JSON (FastAPI).
Evita 500 por ObjectId, Decimal128, datetime, etc.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from bson import ObjectId

try:
    from bson.decimal128 import Decimal128
except ImportError:  # pragma: no cover
    Decimal128 = type(None)  # type: ignore


def mongo_to_json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return str(value)
    if Decimal128 is not type(None) and isinstance(value, Decimal128):
        return float(value.to_decimal())
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except Exception:
            return str(value)
    if isinstance(value, dict):
        return {str(k): mongo_to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [mongo_to_json_safe(v) for v in value]
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return value
    # Fallback: intentar isoformat (p.ej. tipos datetime de terceros)
    if hasattr(value, "isoformat") and callable(value.isoformat):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)
