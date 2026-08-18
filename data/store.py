from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import streamlit as st
from sqlalchemy import text


class CloudConfigError(RuntimeError):
    pass


def get_connection():
    try:
        return st.connection("sql", type="sql")
    except Exception as exc:
        raise CloudConfigError("Cloud PostgreSQL connection is missing or invalid.") from exc


def _decode_json_fields(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    for field in ("blueprint", "production", "distribution", "performance"):
        val = out.get(field)
        if isinstance(val, str):
            try:
                out[field] = json.loads(val)
            except Exception:
                out[field] = {}
        elif val is None:
            out[field] = {}
    return out


def content_id(row_or_id: Any) -> str:
    raw_id = row_or_id.get("id") if isinstance(row_or_id, dict) else row_or_id
    return f"MOR-{int(raw_id):04d}"


def load_stories() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        df = conn.query("select * from public.stories order by id desc", ttl=0)
        return [_decode_json_fields(r) for r in df.to_dict(orient="records")]
    except Exception as exc:
        raise CloudConfigError("Could not read the MORQEVA cloud database. Run db/schema.sql in Supabase first.") from exc


def get_story(story_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    df = conn.query("select * from public.stories where id = :id limit 1", params={"id": story_id}, ttl=0)
    if df.empty:
        return None
    return _decode_json_fields(df.iloc[0].to_dict())


def create_story(payload: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_connection()
    now = datetime.now(timezone.utc)
    params = {
        "seed": payload.get("seed", ""),
        "title": payload.get("title", payload.get("seed", "Untitled")),
        "story_mode": payload.get("story_mode", "VERIFIED_REAL"),
        "country": payload.get("country", ""),
        "status": payload.get("status", "BLUEPRINT_REVIEW"),
        "blueprint": json.dumps(payload.get("blueprint", {}), ensure_ascii=False),
        "production": json.dumps(payload.get("production", {}), ensure_ascii=False),
        "distribution": json.dumps(payload.get("distribution", {}), ensure_ascii=False),
        "performance": json.dumps(payload.get("performance", {}), ensure_ascii=False),
        "updated_at": now,
    }
    sql = text("""
        insert into public.stories
        (seed,title,story_mode,country,status,blueprint,production,distribution,performance,updated_at)
        values
        (:seed,:title,:story_mode,:country,:status,cast(:blueprint as jsonb),cast(:production as jsonb),cast(:distribution as jsonb),cast(:performance as jsonb),:updated_at)
        returning *
    """)
    with conn.session as session:
        row = session.execute(sql, params).mappings().first()
        session.commit()
    return _decode_json_fields(dict(row))


def update_story(story_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {"seed","title","story_mode","country","status","blueprint","production","distribution","performance"}
    assignments = []
    params: Dict[str, Any] = {"id": story_id, "updated_at": datetime.now(timezone.utc)}
    for key, value in fields.items():
        if key not in allowed:
            continue
        if key in {"blueprint","production","distribution","performance"}:
            params[key] = json.dumps(value or {}, ensure_ascii=False)
            assignments.append(f"{key}=cast(:{key} as jsonb)")
        else:
            params[key] = value
            assignments.append(f"{key}=:{key}")
    assignments.append("updated_at=:updated_at")
    sql = text(f"update public.stories set {', '.join(assignments)} where id=:id returning *")
    conn = get_connection()
    with conn.session as session:
        row = session.execute(sql, params).mappings().first()
        session.commit()
    return _decode_json_fields(dict(row)) if row else get_story(story_id)


def delete_story(story_id: int) -> None:
    conn = get_connection()
    with conn.session as session:
        session.execute(text("delete from public.stories where id=:id"), {"id": story_id})
        session.commit()
