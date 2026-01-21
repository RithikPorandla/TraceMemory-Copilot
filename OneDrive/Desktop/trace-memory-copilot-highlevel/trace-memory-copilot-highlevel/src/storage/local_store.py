from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PinnedFact:
    text: str
    source: Optional[str] = None
    rating: Optional[float] = None


class LocalUserStore:
    """Lightweight local persistence for portfolio/demo purposes.

    Stores:
      - known session IDs per user (so we can do diffs)
      - pinned / edited facts ("Memory Cards")

    This intentionally does NOT attempt to mutate Zep memory.
    """

    def __init__(self, base_dir: str = ".tracememory"):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def _user_path(self, user_id: str) -> Path:
        safe = "".join(ch for ch in user_id if ch.isalnum() or ch in ("-", "_"))
        return self.base / f"{safe}.json"

    def _load(self, user_id: str) -> Dict[str, Any]:
        path = self._user_path(user_id)
        if not path.exists():
            return {"sessions": [], "pinned_facts": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def _save(self, user_id: str, data: Dict[str, Any]) -> None:
        path = self._user_path(user_id)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_session(self, user_id: str, session_id: str) -> None:
        data = self._load(user_id)
        # Backwards compatible storage:
        # - older versions stored sessions as a list[str]
        # - new versions store list[dict] with created_at for analytics
        sessions = data.get("sessions", [])

        # Normalize
        norm: List[Dict[str, Any]] = []
        for s in sessions:
            if isinstance(s, str):
                norm.append({"id": s, "created_at": None})
            elif isinstance(s, dict) and s.get("id"):
                norm.append({"id": str(s.get("id")), "created_at": s.get("created_at")})

        if not any(s["id"] == session_id for s in norm):
            from datetime import datetime

            norm.append({"id": session_id, "created_at": datetime.utcnow().isoformat() + "Z"})

        data["sessions"] = norm
        self._save(user_id, data)

    def list_sessions(self, user_id: str) -> List[str]:
        data = self._load(user_id)
        sessions = data.get("sessions", [])
        out: List[str] = []
        for s in sessions:
            if isinstance(s, str):
                out.append(s)
            elif isinstance(s, dict) and s.get("id"):
                out.append(str(s.get("id")))
        return out

    def list_session_records(self, user_id: str) -> List[Dict[str, Any]]:
        """Return session records with timestamps (if available)."""
        data = self._load(user_id)
        sessions = data.get("sessions", [])
        out: List[Dict[str, Any]] = []
        for s in sessions:
            if isinstance(s, str):
                out.append({"id": s, "created_at": None})
            elif isinstance(s, dict) and s.get("id"):
                out.append({"id": str(s.get("id")), "created_at": s.get("created_at")})
        return out

    def set_pinned_facts(self, user_id: str, facts: List[PinnedFact]) -> None:
        data = self._load(user_id)
        data["pinned_facts"] = [fact.__dict__ for fact in facts]
        self._save(user_id, data)

    def get_pinned_facts(self, user_id: str) -> List[PinnedFact]:
        data = self._load(user_id)
        raw = data.get("pinned_facts", [])
        out: List[PinnedFact] = []
        for item in raw:
            if isinstance(item, dict) and item.get("text"):
                out.append(PinnedFact(**item))
        return out
