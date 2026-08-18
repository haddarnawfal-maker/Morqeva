from __future__ import annotations

import html
from typing import Any, Dict

import streamlit as st

from config.settings import APP_NAME, APP_TAGLINE, MASTER_RULES
from data.store import CloudConfigError


def apply_custom_css():
    st.markdown(
        """
<style>
:root { --mq-purple:#8B5CF6; --mq-violet:#6D28D9; --mq-bg:#09090B; --mq-card:#121217; --mq-border:#27272A; }
.block-container {padding-top: 2rem; max-width: 1400px;}
[data-testid="stSidebar"] {background: linear-gradient(180deg,#0b0b10 0%,#111118 100%); border-right:1px solid #24242c;}
.mq-brand {font-size:1.35rem;font-weight:900;letter-spacing:.16em;color:#fff;margin-bottom:.15rem}
.mq-sub {font-size:.70rem;color:#8e8e9a;letter-spacing:.09em;text-transform:uppercase}
.mq-hero {padding:20px 22px;border-radius:18px;background:linear-gradient(135deg,rgba(139,92,246,.18),rgba(17,17,24,.94) 45%,rgba(9,9,11,.98));border:1px solid rgba(139,92,246,.28);margin-bottom:18px}
.mq-kicker {color:#A78BFA;font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;font-weight:800}
.mq-title {font-size:2rem;font-weight:850;line-height:1.05;margin:.25rem 0 .45rem}
.mq-muted {color:#A1A1AA;font-size:.92rem}
.mq-card {padding:16px 17px;border-radius:15px;background:#121217;border:1px solid #27272A;margin-bottom:10px}
.mq-pill {display:inline-block;padding:4px 9px;border-radius:999px;background:#22193b;color:#C4B5FD;font-size:.72rem;font-weight:700;margin-right:5px}
.mq-verified {background:#12301f;color:#86EFAC}.mq-folklore {background:#362912;color:#FDE68A}.mq-fiction {background:#321c36;color:#F0ABFC}.mq-unverified{background:#342516;color:#FDBA74}
[data-testid="stMetric"] {background:#111116;border:1px solid #27272A;padding:14px;border-radius:14px}
.stButton>button {border-radius:11px;font-weight:700}
.stCodeBlock {border-radius:14px!important}
@media(max-width:720px){.block-container{padding:1rem .8rem}.mq-title{font-size:1.55rem}.mq-hero{padding:16px}}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    st.sidebar.markdown(f'<div class="mq-brand">{APP_NAME}</div><div class="mq-sub">{APP_TAGLINE}</div>', unsafe_allow_html=True)
    st.sidebar.markdown("")
    st.sidebar.caption("10 scenes · 60–65 sec · no narration")
    st.sidebar.caption("Flow → Vibes / Symphony → CapCut")
    st.sidebar.divider()


def page_header(title: str, description: str = "", kicker: str = "DARK VAULT"):
    st.markdown(
        f'<div class="mq-hero"><div class="mq-kicker">{html.escape(kicker)}</div><div class="mq-title">{html.escape(title)}</div><div class="mq-muted">{html.escape(description)}</div></div>',
        unsafe_allow_html=True,
    )


def cloud_guard():
    try:
        from data.store import get_connection
        conn = get_connection()
        conn.query("select 1 as ok", ttl=0)
    except Exception:
        st.error("MORQEVA Cloud is not configured yet. Add the Supabase/PostgreSQL connection URL under [connections.sql] in Streamlit Cloud Secrets, then run db/schema.sql once.")
        st.stop()


def status_label(status: str) -> str:
    return (status or "").replace("_", " ").title()


def fact_badge(label: str) -> str:
    cls = {
        "VERIFIED": "mq-verified",
        "FOLKLORE": "mq-folklore",
        "FICTION": "mq-fiction",
        "UNVERIFIED": "mq-unverified",
    }.get(label, "")
    return f'<span class="mq-pill {cls}">{html.escape(label)}</span>'


def production_defaults(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    scenes = blueprint.get("scenes", [])
    return {
        "scenes": {
            str(s.get("scene_number")): {
                "image_done": False,
                "animation_done": False,
                "animation_engine": "Vibes",
                "approved": False,
                "notes": "",
            }
            for s in scenes
        },
        "capcut_done": False,
        "final_duration": 0.0,
        "master_url": "",
    }
