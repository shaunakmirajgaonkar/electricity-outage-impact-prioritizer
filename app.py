
import io
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="GridRelief Local", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

DATA_PATH = Path(__file__).parent / "data" / "outage_zone_registry.csv"

REQUIRED = [
    "zone_id","zone_name","latitude","longitude","hospital_dependency","water_supply_dependency",
    "heat_risk","vulnerable_resident_index","critical_facility_dependency","outage_duration_hours",
    "medical_facility_count","water_facility_count","population_exposed","building_density",
    "road_access_constraint","backup_power_coverage","recent_outage_count"
]

SIGNALS = {
    "Hospital dependency": ("hospital_dependency", 0.16),
    "Water-supply dependency": ("water_supply_dependency", 0.14),
    "Heat risk": ("heat_risk", 0.12),
    "Vulnerable residents": ("vulnerable_resident_index", 0.14),
    "Critical facilities": ("critical_facility_dependency", 0.12),
    "Outage duration": ("outage_duration_hours", 0.14),
    "Population exposed": ("population_exposed", 0.06),
    "Road-access constraint": ("road_access_constraint", 0.05),
    "Recent outages": ("recent_outage_count", 0.03),
    "Backup-power gap": ("backup_power_coverage", 0.04),
}

st.markdown("""
<style>
:root { --ink:#172033; --muted:#657085; --line:#e6eaf0; --panel:#ffffff; --soft:#f5f8fc; --accent:#2563eb; }
.stApp { background: #f7f9fc; color: var(--ink); }
section[data-testid="stSidebar"] { background:#ffffff; border-right:1px solid #e8ecf2; }
.block-container { padding: 2rem 2.4rem 3rem; max-width: 1500px; }
.hero { background:linear-gradient(135deg,#ffffff 0%,#edf5ff 100%); border:1px solid #dfe8f5; border-radius:24px; padding:28px 30px; margin-bottom:20px; }
.kicker { color:#2563eb; font-size:.76rem; font-weight:800; letter-spacing:.13em; text-transform:uppercase; }
h1 { font-size:2.35rem !important; letter-spacing:-.04em; color:#172033 !important; }
h2,h3 { color:#172033 !important; }
.card { background:#fff; border:1px solid #e6eaf0; border-radius:18px; padding:20px; box-shadow:0 4px 18px rgba(31,41,55,.04); }
.metric { font-size:1.85rem; font-weight:800; color:#172033; }
.label { color:#657085; font-size:.82rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; }
.notice { background:#fff8e8; border:1px solid #f3dfaa; border-radius:14px; padding:14px 16px; color:#6a5318; }
.info { background:#eef6ff; border:1px solid #cfe3ff; border-radius:14px; padding:14px 16px; color:#174a82; }
[data-testid="stMetric"] { background:#fff; border:1px solid #e6eaf0; padding:16px; border-radius:16px; }
div[data-baseweb="select"] > div { background:#fff; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(uploaded=None):
    if uploaded is None:
        x = pd.read_csv(DATA_PATH)
    else:
        x = pd.read_csv(uploaded)
    missing = [c for c in REQUIRED if c not in x.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    for c in REQUIRED[2:]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    if x[REQUIRED[2:]].isna().any().any():
        raise ValueError("One or more numeric fields contain missing/non-numeric values.")
    return x

def norm(s):
    lo, hi = s.min(), s.max()
    if hi == lo: return pd.Series(50.0, index=s.index)
    return ((s-lo)/(hi-lo)*100).clip(0,100)

def score_row(r):
    parts = {}
    for label,(col,w) in SIGNALS.items():
        if col == "outage_duration_hours":
            v = min(float(r[col])/24*100,100)
        elif col == "backup_power_coverage":
            v = 100-float(r[col])  # less backup = greater restoration priority
        elif col == "recent_outage_count":
            v = min(float(r[col])/10*100,100)
        else:
            v = float(r[col])
        parts[label] = v*w
    score = float(np.clip(sum(parts.values()),0,100))
    if score >= 75: cls = "Critical"
    elif score >= 55: cls = "High"
    elif score >= 30: cls = "Moderate"
    else: cls = "Low"
    return score, cls, parts

def add_scores(x):
    out=x.copy()
    result=out.apply(lambda r: score_row(r), axis=1)
    out["priority_score"]=[z[0] for z in result]
    out["classification"]=[z[1] for z in result]
    return out

try:
    if "upload" not in st.session_state:
        st.session_state.upload = None
    DF = load_data(st.session_state.upload)
except Exception as e:
    st.error(f"Dataset validation failed: {e}")
    st.stop()

SCORES = add_scores(DF)

with st.sidebar:
    st.markdown("### ⚡ GridRelief Local")
    st.caption("Electricity outage impact prioritization")
    page = st.radio("Workspace", ["Command Center","Zone Review","Priority Queue","Analytics","Data Lab"], label_visibility="collapsed")
    st.divider()
    st.markdown("**LOCAL-FIRST**")
    st.caption("No external APIs • transparent scoring • human review")
    st.divider()
    st.caption(f"{len(SCORES)} local outage zones loaded")

if page == "Command Center":
    st.markdown('<div class="hero"><div class="kicker">GRID IMPACT INTELLIGENCE · NO API · EXPLAINABLE</div><h1>⚡ Electricity Outage Impact Prioritizer</h1><p>Local-first decision support for identifying outage zones that may warrant earlier restoration attention using critical-service dependency, heat exposure, vulnerable residents, outage duration, access constraints, and backup-power signals.</p></div>', unsafe_allow_html=True)
    a,b,c,d=st.columns(4)
    a.metric("Zones monitored",len(SCORES))
    b.metric("Critical priority",int((SCORES.classification=="Critical").sum()))
    c.metric("High priority",int((SCORES.classification=="High").sum()))
    d.metric("Average priority",f"{SCORES.priority_score.mean():.1f}/100")
    st.write("")
    left,right=st.columns([1.35,1])
    with left:
        st.markdown("### Restoration priority landscape")
        fig=px.bar(SCORES.sort_values("priority_score",ascending=True),x="priority_score",y="zone_name",orientation="h",text="priority_score",labels={"priority_score":"Priority score","zone_name":"Zone"})
        fig.update_traces(texttemplate="%{text:.1f}",textposition="outside")
        fig.update_layout(height=500,margin=dict(l=10,r=40,t=20,b=20),paper_bgcolor="white",plot_bgcolor="white")
        st.plotly_chart(fig,use_container_width=True)
    with right:
        st.markdown("### What drives priority?")
        vals={}
        for label,(_,w) in SIGNALS.items(): vals[label]=float(SCORES.apply(lambda r: score_row(r)[2][label],axis=1).mean())
        s=pd.Series(vals).sort_values(ascending=True)
        fig2=px.bar(x=s.values,y=s.index,orientation="h",labels={"x":"Average contribution","y":""})
        fig2.update_layout(height=500,margin=dict(l=10,r=20,t=20,b=20),paper_bgcolor="white",plot_bgcolor="white")
        st.plotly_chart(fig2,use_container_width=True)
    st.markdown('<div class="notice"><b>Human-review notice:</b> priority scores do not determine who receives electricity first. They are screening signals to support utility, emergency-management, and field teams. Confirm live grid conditions, critical-service status, safety constraints, and applicable restoration protocols.</div>',unsafe_allow_html=True)

elif page == "Zone Review":
    st.markdown("## Zone Review")
    zid=st.selectbox("Select outage zone",SCORES.zone_id.tolist())
    r=SCORES[SCORES.zone_id==zid].iloc[0]
    score,cls,parts=score_row(r)
    st.markdown(f"### {r.zone_name}")
    a,b,c=st.columns(3)
    a.metric("Impact priority score",f"{score:.1f}/100")
    b.metric("Classification",cls)
    c.metric("Outage duration",f"{r.outage_duration_hours:.1f} h")
    st.write("")
    st.markdown("### Contributing signals")
    top=sorted(parts.items(),key=lambda z:z[1],reverse=True)
    for label,val in top[:6]:
        st.markdown(f'<div class="card" style="margin-bottom:9px"><b>{label}</b><br><span style="color:#657085">Contribution to priority</span><span style="float:right;font-weight:800">{val:.1f} pts</span></div>',unsafe_allow_html=True)
    st.markdown("### Zone context")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Hospitals / dependency",f"{r.hospital_dependency:.0f}")
    c2.metric("Water dependency",f"{r.water_supply_dependency:.0f}")
    c3.metric("Heat risk",f"{r.heat_risk:.0f}")
    c4.metric("Vulnerable residents",f"{r.vulnerable_resident_index:.0f}")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Critical facilities",f"{r.critical_facility_dependency:.0f}")
    c2.metric("Population exposed",f"{r.population_exposed:.0f}")
    c3.metric("Road constraint",f"{r.road_access_constraint:.0f}")
    c4.metric("Backup coverage",f"{r.backup_power_coverage:.0f}%")
    action = {"Critical":"Escalate for immediate human review of critical services, outage duration, safe access, and restoration constraints.",
              "High":"Prioritize operational review and verify critical-service dependency and backup-power coverage.",
              "Moderate":"Review local conditions and monitor outage duration and vulnerable-service exposure.",
              "Low":"Continue routine monitoring and confirm conditions through normal outage-management workflows."}[cls]
    st.markdown(f'<div class="info"><b>Suggested review focus:</b> {action}</div>',unsafe_allow_html=True)

elif page == "Priority Queue":
    st.markdown("## Priority Queue")
    threshold=st.slider("Show zones at or above this priority score",0,100,55,1)
    V=SCORES[SCORES.priority_score>=threshold].sort_values("priority_score",ascending=False)
    a,b,c=st.columns(3)
    a.metric("Threshold",f"{threshold}/100")
    b.metric("Zones in queue",len(V))
    c.metric("Critical + High",int(SCORES.classification.isin(["Critical","High"]).sum()))
    if V.empty:
        st.info("No zones meet the selected threshold. Increase the threshold? Actually, lower the threshold to broaden the queue.")
    else:
        st.dataframe(V[["zone_id","zone_name","priority_score","classification","outage_duration_hours","population_exposed","hospital_dependency","water_supply_dependency","heat_risk"]],hide_index=True,use_container_width=True)
        st.download_button("Download priority queue CSV",V.to_csv(index=False).encode(),file_name="outage_priority_queue.csv",mime="text/csv")
    st.markdown('<div class="notice"><b>Important:</b> A queue score is not an automatic restoration order and should not override live emergency, safety, grid-stability, or regulatory procedures.</div>',unsafe_allow_html=True)

elif page == "Analytics":
    st.markdown("## Analytics Studio")
    x,y=st.columns(2)
    with x:
        fig=px.scatter(SCORES,x="outage_duration_hours",y="priority_score",size="population_exposed",color="classification",hover_name="zone_name",labels={"outage_duration_hours":"Outage duration (hours)","priority_score":"Priority score"})
        fig.update_layout(height=430,paper_bgcolor="white",plot_bgcolor="white")
        st.plotly_chart(fig,use_container_width=True)
    with y:
        long=SCORES.melt(id_vars=["zone_name"],value_vars=["hospital_dependency","water_supply_dependency","heat_risk","vulnerable_resident_index","critical_facility_dependency"],var_name="signal",value_name="index")
        fig=px.box(long,x="signal",y="index",points="all",labels={"signal":"Signal","index":"Index"})
        fig.update_layout(height=430,paper_bgcolor="white",plot_bgcolor="white")
        st.plotly_chart(fig,use_container_width=True)
    st.markdown("### Local spatial view")
    fig=px.scatter_map(SCORES,lat="latitude",lon="longitude",color="priority_score",size="population_exposed",hover_name="zone_name",zoom=11,height=560)
    fig.update_layout(map_style="open-street-map",margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig,use_container_width=True)

else:
    st.markdown("## Data Lab")
    st.markdown("### Required CSV columns")
    st.code(", ".join(REQUIRED))
    st.success("Current local dataset is valid.")
    upload=st.file_uploader("Optional: replace local outage-zone dataset",type=["csv"],help="Maximum 200MB. Use synthetic or appropriately anonymized operational data.")
    if upload is not None:
        try:
            newdf=load_data(upload)
            st.session_state.upload=upload.getvalue()
            DF=newdf; SCORES=add_scores(DF)
            st.success(f"Loaded {len(DF)} local records successfully.")
        except Exception as e:
            st.error(str(e))
    st.dataframe(DF,use_container_width=True,hide_index=True)
    st.download_button("Download scored outage dataset",SCORES.to_csv(index=False).encode(),file_name="scored_outage_zones.csv",mime="text/csv")
    st.caption(f"Local processing only • {len(DF)} records • Score range {SCORES.priority_score.min():.1f}–{SCORES.priority_score.max():.1f}")

st.markdown("---")
st.caption("GridRelief Local • 100% local processing • No external APIs • Electricity outage impact decision support")
