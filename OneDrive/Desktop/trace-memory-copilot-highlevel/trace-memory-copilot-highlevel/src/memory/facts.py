from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional


@dataclass
class FactItem:
    text: str
    rating: Optional[float] = None
    source: Optional[str] = None


def _coerce_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def extract_fact_items(memory: Any) -> list[FactItem]:
    """Best-effort extraction of "facts" from a Zep Memory response.

    Zep SDK response shapes can differ across versions and deployment modes.
    This helper keeps the UI stable by supporting:
      - memory.facts (object or dict items)
      - a fallback to parsing memory.context for bullet-like lines
    """

    items: list[FactItem] = []

    raw_facts = getattr(memory, "facts", None)
    if raw_facts:
        for f in _iter(raw_facts):
            text = _get(f, "fact") or _get(f, "content") or _get(f, "text")
            text = (text or "").strip()
            if not text:
                continue

            rating = _coerce_float(_get(f, "rating"))
            source = (_get(f, "source") or "").strip() or None
            items.append(FactItem(text=text, rating=rating, source=source))

        if items:
            return items

    # Fallback: parse memory.context
    ctx = (getattr(memory, "context", None) or "").strip()
    if not ctx:
        return items

    lines = [ln.strip() for ln in ctx.splitlines() if ln.strip()]
    for ln in lines:
        ln = re.sub(r"^[-*•]\s+", "", ln)
        ln = re.sub(r"^\d+\.?\s+", "", ln)
        if len(ln) >= 8:
            items.append(FactItem(text=ln))

    return items


def _iter(value: Any) -> Iterable[Any]:
    if isinstance(value, (list, tuple)):
        return value
    return [value]


def _get(obj: Any, key: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)
