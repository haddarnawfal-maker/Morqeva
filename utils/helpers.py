from __future__ import annotations

import html
from typing import Any, Dict

import streamlit as st

from config.settings import APP_NAME, APP_TAGLINE


def apply_custom_css():
    st.markdown("""
<style>
:root{--mq-purple:#8B5CF6;--mq-violet:#6D28D9;--mq-bg:#08090d;--mq-card:#111219;--mq-border:#282a36;--mq-text:#f5f5f7;--mq-muted:#9295a5;--mq-green:#22c55e;--mq-amber:#f59e0b;--mq-red:#ef4444}
.stApp{background:radial-gradient(circle at 65% -20%,rgba(109,40,217,.16),transparent 35%),#08090d;color:var(--mq-text)}
.block-container{padding-top:1.2rem;padding-bottom:4rem;max-width:1440px}
[data-testid="stSidebar"]{background:#0b0c11;border-right:1px solid #20222b}[data-testid="stSidebarNav"] span{font-weight:650}
.mq-brand{font-size:1.35rem;font-weight:950;letter-spacing:.2em;color:#fff}.mq-sub{font-size:.66rem;color:#7f8291;letter-spacing:.11em;text-transform:uppercase}.mq-live{display:flex;align-items:center;gap:7px;color:#9699a7;font-size:.7rem;margin-top:10px}.mq-dot{width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 12px rgba(34,197,94,.75);animation:mqPulse 2s infinite}@keyframes mqPulse{50%{opacity:.35}}
.mq-hero{position:relative;overflow:hidden;padding:24px 27px;border-radius:20px;background:linear-gradient(120deg,rgba(109,40,217,.27),rgba(17,18,25,.97) 42%,rgba(8,9,13,.98));border:1px solid rgba(139,92,246,.3);margin-bottom:17px;box-shadow:0 20px 55px rgba(0,0,0,.22)}.mq-hero:after{content:'';position:absolute;width:260px;height:260px;border-radius:50%;right:-100px;top:-150px;background:rgba(139,92,246,.16);filter:blur(12px)}
.mq-kicker{color:#b69cff;font-size:.7rem;text-transform:uppercase;letter-spacing:.17em;font-weight:850}.mq-title{font-size:2.05rem;font-weight:900;line-height:1.05;margin:.28rem 0 .45rem;letter-spacing:-.04em}.mq-muted{color:#9699a8;font-size:.9rem}.mq-section{display:flex;justify-content:space-between;align-items:end;margin:24px 0 10px}.mq-section h3{margin:0;font-size:1.05rem}.mq-section span{font-size:.72rem;color:#7e8190}
.mq-card{padding:16px 17px;border-radius:16px;background:linear-gradient(145deg,#12131a,#0e0f15);border:1px solid #272934;margin-bottom:10px;box-shadow:0 8px 28px rgba(0,0,0,.12)}.mq-card:hover{border-color:#44375f}.mq-pill{display:inline-flex;align-items:center;padding:4px 9px;border-radius:999px;background:#251b40;color:#c4b5fd;font-size:.67rem;font-weight:800;margin-right:5px}.mq-verified{background:#12301f;color:#86efac}.mq-folklore{background:#362912;color:#fde68a}.mq-fiction{background:#321c36;color:#f0abfc}.mq-unverified{background:#342516;color:#fdba74}
.mq-topgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.mq-stat{padding:15px 16px;border-radius:15px;background:#111219;border:1px solid #272934}.mq-stat b{font-size:1.55rem;display:block;letter-spacing:-.04em}.mq-stat small{color:#858897;text-transform:uppercase;letter-spacing:.08em;font-size:.62rem}.mq-pipeline{display:grid;grid-template-columns:repeat(6,1fr);gap:7px}.mq-stage{position:relative;padding:12px;border:1px solid #292b36;border-radius:13px;background:#101118}.mq-stage strong{display:block;font-size:1.15rem}.mq-stage span{color:#858897;font-size:.65rem;text-transform:uppercase;letter-spacing:.08em}.mq-stage.active{border-color:#6847a9;background:linear-gradient(145deg,#1b1430,#111219)}
.mq-story{padding:15px 16px;border:1px solid #272934;border-radius:15px;background:#101118;margin-bottom:9px}.mq-story-head{display:flex;justify-content:space-between;gap:12px}.mq-story h4{font-size:.98rem;margin:.6rem 0 .25rem}.mq-progress{height:5px;background:#20222b;border-radius:99px;overflow:hidden;margin-top:11px}.mq-progress i{display:block;height:100%;background:linear-gradient(90deg,#6d28d9,#a78bfa);border-radius:99px}.mq-quota{height:7px;background:#20222b;border-radius:99px;overflow:hidden;margin:8px 0}.mq-quota>div{height:100%;border-radius:99px;background:linear-gradient(90deg,#6d28d9,#a78bfa)}
.mq-health{display:flex;align-items:center;justify-content:space-between;padding:11px 0;border-bottom:1px solid #23252e}.mq-health:last-child{border:0}.mq-health b{font-size:.82rem}.mq-health span{font-size:.7rem;color:#86efac}
[data-testid="stMetric"]{background:#111219;border:1px solid #272934;padding:14px;border-radius:15px}[data-testid="stMetricLabel"]{color:#8e91a0}[data-testid="stMetricValue"]{font-weight:850;letter-spacing:-.03em}.stButton>button,.stLinkButton>a{border-radius:11px!important;font-weight:750;min-height:40px;transition:.15s}.stButton>button:hover,.stLinkButton>a:hover{transform:translateY(-1px)}.stCodeBlock{border-radius:13px!important}[data-testid="stExpander"],[data-testid="stForm"]{border-radius:15px!important;border-color:#292b36!important;background:rgba(17,18,25,.66)}div[data-baseweb="tab-list"]{gap:4px}button[data-baseweb="tab"]{border-radius:9px;padding-left:13px;padding-right:13px}
@media(max-width:760px){.block-container{padding:1rem .72rem 3rem}.mq-title{font-size:1.55rem}.mq-hero{padding:17px 18px;border-radius:16px}.mq-topgrid{grid-template-columns:repeat(2,1fr)}.mq-pipeline{grid-template-columns:repeat(3,1fr)}.mq-story-head{display:block}[data-testid="stHorizontalBlock"]{gap:.45rem}.mq-muted{font-size:.82rem}.mq-section{margin-top:18px}}
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
