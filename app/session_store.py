from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.firestore import get_db

SESSIONS_COL = "lf_sessions"
FIRESTORE_TIMEOUT = 10


# ----------------------------
# Internal helpers
# ----------------------------
def _build_doc_id(passenger_id: str, session_id: str) -> str:
    passenger_id = str(passenger_id or "").strip()
    session_id = str(session_id or "").strip()
    return f"{passenger_id}_{session_id}"


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_data(data: Any) -> Dict[str, Any]:
    return data if isinstance(data, dict) else {}


# ----------------------------
# Public API
# ----------------------------
def get_session(passenger_id: str, session_id: str) -> Dict[str, Any]:
    print("GET_SESSION START", flush=True)

    db = get_db()
    doc_id = _build_doc_id(passenger_id, session_id)

    print(f"GET_SESSION DOC_ID = {doc_id}", flush=True)
    print("GET_SESSION BEFORE FIRESTORE GET", flush=True)

    doc_ref = db.collection(SESSIONS_COL).document(doc_id)
    doc = doc_ref.get(timeout=FIRESTORE_TIMEOUT)

    print("GET_SESSION AFTER FIRESTORE GET", flush=True)

    if not doc.exists:
        print("GET_SESSION DOC NOT FOUND - RETURN MENU", flush=True)
        return {"state": "menu", "data": {}, "updated_at": None}

    session = doc.to_dict() or {}

    print("GET_SESSION DOC LOADED", session, flush=True)

    return {
        "state": str(session.get("state") or "menu"),
        "data": _normalize_data(session.get("data")),
        "updated_at": session.get("updated_at"),
    }


def save_session(
    passenger_id: str,
    session_id: str,
    state: str,
    data: Optional[Dict[str, Any]] = None
) -> None:
    print("SAVE_SESSION START", flush=True)

    db = get_db()
    doc_id = _build_doc_id(passenger_id, session_id)

    payload = {
        "state": str(state or "menu"),
        "data": _normalize_data(data),
        "updated_at": _now_utc_iso(),
    }

    print(f"SAVE_SESSION DOC_ID = {doc_id}", flush=True)
    print("SAVE_SESSION BEFORE FIRESTORE SET", payload, flush=True)

    db.collection(SESSIONS_COL).document(doc_id).set(
        payload,
        merge=True,
        timeout=FIRESTORE_TIMEOUT,
    )

    print("SAVE_SESSION AFTER FIRESTORE SET", flush=True)


def reset_session(passenger_id: str, session_id: str) -> None:
    print("RESET_SESSION START", flush=True)
    save_session(passenger_id, session_id, "menu", {})
    print("RESET_SESSION DONE", flush=True)


def delete_session(passenger_id: str, session_id: str) -> None:
    print("DELETE_SESSION START", flush=True)

    db = get_db()
    doc_id = _build_doc_id(passenger_id, session_id)

    print(f"DELETE_SESSION DOC_ID = {doc_id}", flush=True)
    print("DELETE_SESSION BEFORE FIRESTORE DELETE", flush=True)

    db.collection(SESSIONS_COL).document(doc_id).delete(
        timeout=FIRESTORE_TIMEOUT,
    )

    print("DELETE_SESSION AFTER FIRESTORE DELETE", flush=True)
