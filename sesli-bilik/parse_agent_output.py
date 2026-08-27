"""Normalize the LangChain Agent JSON payload used by the n8n Code node."""

from __future__ import annotations

import json
import re
from typing import Any

ALLOWED_STATUS = ("ask_topic", "question", "stats", "finished", "reset")
FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _unwrap(root: Any) -> Any:
    data = root.get("output", root) if isinstance(root, dict) else root
    if isinstance(data, str):
        trimmed = FENCE_RE.sub("", data.strip())
        try:
            data = json.loads(trimmed)
        except json.JSONDecodeError:
            data = {"status": "ask_topic", "reply_text": trimmed or "Zəhmət olmasa təkrar edin."}
    if (
        isinstance(data, dict)
        and isinstance(data.get("output"), dict)
        and data["output"].get("status")
    ):
        data = data["output"]
    return data if isinstance(data, dict) else {}


def parse_agent_output(root: Any, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    """Flatten agent output into the routing fields the Switch node expects."""
    ctx = ctx or {}
    data = _unwrap(root)
    status = data.get("status") if data.get("status") in ALLOWED_STATUS else "ask_topic"
    reply_text = str(data.get("reply_text") or "Zəhmət olmasa təkrar edin.")[:4000]
    chat_id = ctx.get("chat_id") or ""
    try:
        score = float(data.get("score", 0))
    except (TypeError, ValueError):
        score = 0.0
    try:
        question_number = float(data.get("question_number", 0))
    except (TypeError, ValueError):
        question_number = 0.0
    is_correct = data.get("is_correct")
    if is_correct is not True and is_correct is not False:
        is_correct = None
    return {
        "status": status,
        "reply_text": reply_text,
        "score": score,
        "question_number": question_number,
        "topic": str(data.get("topic") or "ümumi bilik"),
        "difficulty": str(data.get("difficulty") or "orta"),
        "is_correct": is_correct,
        "game_over": bool(data.get("game_over")) or status == "finished",
        "chat_id": str(chat_id),
        "session_key": ctx.get("session_key") or f"trivia_{chat_id}",
        "user_text": ctx.get("user_text") or "",
        "source": ctx.get("source") or "text",
    }
