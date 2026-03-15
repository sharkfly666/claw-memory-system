from __future__ import annotations

from typing import Any


def _message_role(message: Any) -> str:
    if isinstance(message, dict):
        return str(message.get("role") or message.get("type") or "").lower()
    return ""


def _message_text(message: Any) -> str:
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"].strip())
            return "\n".join(part for part in parts if part)
        text = message.get("text")
        if isinstance(text, str):
            return text.strip()
    return ""


def extract_turn_texts(messages: list[Any]) -> dict[str, str]:
    user_parts: list[str] = []
    assistant_parts: list[str] = []
    tool_parts: list[str] = []

    for message in messages:
        role = _message_role(message)
        text = _message_text(message)
        if not text:
            continue
        if role == "user":
            user_parts.append(text)
        elif role == "assistant":
            assistant_parts.append(text)
        elif role == "tool":
            tool_parts.append(text)

    return {
        "user_text": "\n".join(user_parts).strip(),
        "assistant_text": "\n".join(assistant_parts).strip(),
        "tool_summary": "\n".join(tool_parts).strip(),
    }
