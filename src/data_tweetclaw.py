import io
import json
from typing import Any

import pandas as pd


TEXT_FIELDS = ("text", "full_text", "tweet_text", "tweet", "content", "body", "message")
TIME_FIELDS = ("created_at", "createdAt", "timestamp", "date", "time", "published_at")
ID_FIELDS = ("id", "tweet_id", "tweetId", "status_id", "post_id")
AUTHOR_FIELDS = ("author", "username", "screen_name", "author_username", "authorUsername", "user")
LIKE_FIELDS = ("like_count", "likes", "favorite_count", "favoriteCount")


def _first(row: dict[str, Any], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = row.get(field)
        if isinstance(value, dict):
            nested = _first(value, AUTHOR_FIELDS)
            if nested:
                return nested
        elif value is not None:
            if pd.api.types.is_scalar(value) and pd.isna(value):
                continue
            text = str(value).strip()
            if text:
                return text
    return ""


def _int_value(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _extract_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if not isinstance(value, dict):
        return []
    for key in ("data", "items", "results", "tweets", "posts", "replies", "records"):
        rows = _extract_rows(value.get(key))
        if rows:
            return rows
    return [value]


def _read_uploaded_file(uploaded_file, filename: str) -> list[dict[str, Any]]:
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content = uploaded_file.getvalue()
    if suffix == "csv":
        return pd.read_csv(io.BytesIO(content)).to_dict(orient="records")
    text = content.decode("utf-8")
    if suffix in {"jsonl", "ndjson"}:
        rows: list[dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    rows.append(parsed)
        return rows
    if suffix == "json":
        return _extract_rows(json.loads(text))
    raise ValueError("Upload a TweetClaw CSV, JSON, JSONL, or NDJSON file.")


def load_tweetclaw_export(uploaded_file, filename: str) -> pd.DataFrame:
    rows = _read_uploaded_file(uploaded_file, filename)
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        text = _first(row, TEXT_FIELDS)
        if not text:
            continue
        tweet_id = _first(row, ID_FIELDS) or f"tweetclaw-{index}"
        normalized.append(
            {
                "comment_id": tweet_id,
                "video_id": _first(row, ID_FIELDS),
                "author": _first(row, AUTHOR_FIELDS),
                "text": text,
                "published_at": _first(row, TIME_FIELDS),
                "like_count": _int_value(_first(row, LIKE_FIELDS)),
                "platform": "tweetclaw",
                "post_id": tweet_id,
            }
        )
    if not normalized:
        raise ValueError("No tweet text rows found in the TweetClaw export.")
    return pd.DataFrame(normalized)
