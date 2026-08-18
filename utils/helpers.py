from __future__ import annotations

import html
from typing import Any, Dict

import streamlit as st

from config.settings import APP_NAME, APP_TAGLINE


def apply_custom_css():
    st.markdown("""
<style>
:root{--mq-purple:#8B5CF6;--mq-violet:#6D28D9;--mq-bg:#07070a;--mq-card:#111116;--mq-border:#292932;--mq-text:#f4f4f5;--mq-muted:#9696a3;--mq-green:#22c55e;--mq-amber:#f59e0b;--mq-red:#ef4444}
.stApp{background:radial-gradient(circle at 72% -10%,rgba(109,40,217,.12),transparent 32%),linear-gradient(180deg,#08080c 0%,#07070a 100%)}
.block-container{padding-top:1.4rem;padding-bottom:4rem;max-width:1480px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#09090e,#0e0e14);border-right:1px solid #24242c}
[data-testid="stSidebarNav"] span{font-weight:650}
.mq-brand{font-size:1.45rem;font-weight:950;letter-spacing:.18em;color:#fff;margin-bottom:.12rem}.mq-sub{font-size:.68rem;color:#81818e;letter-spacing:.11em;text-transform:uppercase}
.mq-live{display:flex;align-items:center;gap:7px;color:#a1a1aa;font-size:.72rem;margin-top:12px}.mq-dot{width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 12px rgba(34,197,94,.75);animation:mqPulse 2s infinite}@keyframes mqPulse{0%,100%{opacity:1}50%{opacity:.35}}
.mq-hero{position:relative;overflow:hidden;padding:25px 27px;border-radius:20px;background:linear-gradient(125deg,rgba(109,40,217,.24),rgba(17,17,24,.96) 43%,rgba(8,8,12,.98));border:1px solid rgba(139,92,246,.3);margin-bottom:18px;box-shadow:0 16px 50px rgba(0,0,0,.18)}.mq-hero:after{content:'';position:absolute;width:220px;height:220px;border-radius:50%;right:-80px;top:-120px;background:rgba(139,92,246,.13);filter:blur(8px)}
.mq-kicker{color:#b49bff;font-size:.72rem;text-transform:uppercase;letter-spacing:.15em;font-weight:850}.mq-title{font-size:2.15rem;font-weight:900;line-height:1.04;margin:.3rem 0 .5rem;letter-spacing:-.035em}.mq-muted{color:#a1a1aa;font-size:.92rem;max-width:850px}
.mq-card{padding:17px 18px;border-radius:16px;background:linear-gradient(145deg,#121218,#0f0f14);border:1px solid #292932;margin-bottom:11px;transition:.18s ease}.mq-card:hover{border-color:#3d3555;transform:translateY(-1px)}
.mq-pill{display:inline-flex;align-items:center;padding:4px 9px;border-radius:999px;background:#22193b;color:#c4b5fd;font-size:.7rem;font-weight:750;margin-right:5px}.mq-verified{background:#12301f;color:#86efac}.mq-folklore{background:#362912;color:#fde68a}.mq-fiction{background:#321c36;color:#f0abfc}.mq-unverified{background:#342516;color:#fdba74}
.mq-pipeline{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin:10px 0 20px}.mq-stage{padding:12px 10px;border:1px solid #292932;border-radius:13px;background:#101015;text-align:center}.mq-stage strong{display:block;font-size:1.1rem}.mq-stage span{color:#8f8f9c;font-size:.68rem;text-transform:uppercase;letter-spacing:.07em}
.mq-quota{height:8px;background:#202028;border-radius:99px;overflow:hidden;margin:8px 0}.mq-quota>div{height:100%;border-radius:99px;background:linear-gradient(90deg,#6d28d9,#a78bfa)}
[data-testid="stMetric"]{background:linear-gradient(145deg,#121218,#0f0f14);border:1px solid #292932;padding:15px;border-radius:15px;box-shadow:0 8px 30px rgba(0,0,0,.12)}[data-testid="stMetricLabel"]{color:#9898a5}[data-testid="stMetricValue"]{font-weight:850;letter-spacing:-.03em}
.stButton>button{border-radius:12px;font-weight:750;min-height:42px;transition:.15s ease}.stButton>button:hover{transform:translateY(-1px)}.stCodeBlock{border-radius:14px!important}
[data-testid="stExpander"], [data-testid="stForm"]{border-radius:15px!important;border-color:#292932!important;background:rgba(17,17,22,.6)}
div[data-baseweb="tab-list"]{gap:5px}button[data-baseweb="tab"]{border-radius:10px;padding-left:14px;padding-right:14px}
@media(max-width:760px){.block-container{padding:1rem .72rem 3rem}.mq-title{font-size:1.65rem}.mq-hero{padding:18px}.mq-pipeline{grid-template-columns:repeat(2,1fr)}[data-testid="stHorizontalBlock"]{gap:.55rem}.mq-muted{font-size:.84rem}}
</style>""",unsafe_allow_html=True)


def render_sidebar():
    st.sidebar.markdown(f'<div class="mq-brand">{APP_NAME}</div><div class="mq-sub">{APP_TAGLINE}</div><div class="mq-live"><i class="mq-dot"></i> CLOUD STUDIO ONLINE</div>',unsafe_allow_html=True)
    st.sidebar.markdown("")
    st.sidebar.caption("10 scenes · 60–65 sec · no narration")
    st.sidebar.caption("Flow → Vibes / Symphony → CapCut")
    st.sidebar.divider()


def page_header(title:str,description:str="",kicker:str="DARK VAULT"):
    st.markdown(f'<div class="mq-hero"><div class="mq-kicker">{html.escape(kicker)}</div><div class="mq-title">{html.escape(title)}</div><div class="mq-muted">{html.escape(description)}</div></div>',unsafe_allow_html=True)


def cloud_guard():
    try:
        from data.store import get_connection
        get_connection().query("select 1 as ok",ttl=0)
    except Exception:
        st.error("MORQEVA Cloud is not configured yet. Add the Supabase/PostgreSQL connection URL under [connections.sql] in Streamlit Cloud Secrets, then run db/schema.sql once.")
        st.stop()


def status_label(status:str)->str:return (status or "").replace("_"," ").title()

def fact_badge(label:str)->str:
    cls={"VERIFIED":"mq-verified","FOLKLORE":"mq-folklore","FICTION":"mq-fiction","UNVERIFIED":"mq-unverified"}.get(label,"")
    return f'<span class="mq-pill {cls}">{html.escape(label)}</span>'


def production_defaults(blueprint:Dict[str,Any])->Dict[str,Any]:
    return {"scenes":{str(s.get("scene_number")):{"image_done":False,"animation_done":False,"animation_engine":"Vibes","approved":False,"notes":""} for s in blueprint.get("scenes",[])},"capcut_done":False,"final_duration":0.0,"master_url":""}
