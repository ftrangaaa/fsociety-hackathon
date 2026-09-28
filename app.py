import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Grid Ghost", page_icon="⚡", layout="wide")

st.markdown('''
<style>
.stApp{background:#07111f;color:#e8eef7}
section[data-testid="stSidebar"]{background:#091522}
.block-container{max-width:1400px;padding-top:2rem}
.hero{padding:30px;border-radius:22px;background:linear-gradient(135deg,#10253d,#081624);border:1px solid #203b58;margin-bottom:22px}
.hero h1{font-size:42px;margin:0;font-weight:800}
.hero p{color:#9fb1c8}
.card{padding:20px;border-radius:18px;background:#0c1a2a;border:1px solid #1b3047;min-height:110px}
.label{color:#8ea3bb;font-size:12px;text-transform:uppercase;font-weight:700}
.value{font-size:30px;font-weight:800;margin-top:6px}
.note{padding:15px 18px;border-radius:14px;background:#0c2034;border:1px solid #23476a;color:#b9cbe0}
</style>
''', unsafe_allow_html=True)

def find_file(*names):
    for n in names:
        if os.path.exists(n):
            return n
    return None

def col(df, names):
    lower={str(x).lower():x for x in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    for x in df.columns:
        if any(n.lower() in str(x).lower() for n in names):
            return x
    return None

def level(x):
    if pd.isna(x): return "UNKNOWN"
    if x >= .70: return "HIGH"
    if x >= .40: return "MEDIUM"
    return "LOW"

risk_file=find_file("improved_risk_scores.csv","model_risk_scores.csv")
date_file=find_file("improved_theft_dates.csv","model_theft_dates.csv")

if not risk_file:
    st.error("Put improved_risk_scores.csv in the same folder as app.py.")
    st.stop()

risk=pd.read_csv(risk_file)
dates=pd.read_csv(date_file) if date_file else pd.DataFrame()

idc=col(risk,["consumer_id","meter_id","meter","consumer","id"])
scorec=col(risk,["risk_score","risk","score","probability"])

if idc is None:
    risk["_consumer_id"]=np.arange(len(risk))
    idc="_consumer_id"
if scorec is None:
    nums=risk.select_dtypes(include=np.number).columns.tolist()
    nums=[x for x in nums if x != idc]
    if not nums:
        st.error("No numeric risk-score column found.")
        st.stop()
    scorec=nums[0]

risk[scorec]=pd.to_numeric(risk[scorec],errors="coerce")
risk["Risk Level"]=risk[scorec].apply(level)

did=col(dates,["consumer_id","meter_id","meter","consumer","id"]) if len(dates) else None
dd=col(dates,["estimated_theft_start_date","theft_start_date","theft_date","start_date","date"]) if len(dates) else None

with st.sidebar:
    st.markdown("## ⚡ GRID GHOST")
    st.caption("Power Distribution Intelligence")
    page=st.radio("Navigation",["Command Center","Consumer Search","Inspection Queue","Timeline","About"])
    st.divider()
    st.caption("HIGH ≥ 0.70")
    st.caption("MEDIUM 0.40–0.69")
    st.caption("LOW < 0.40")

st.markdown('''
<div class="hero">
<h1>⚡ Grid Ghost</h1>
<p>AI-assisted intelligence for suspicious smart-meter behavior and anomaly timelines.</p>
</div>
''', unsafe_allow_html=True)

if page=="Command Center":
    total=len(risk); high=(risk["Risk Level"]=="HIGH").sum(); med=(risk["Risk Level"]=="MEDIUM").sum()
    avg=risk[scorec].mean()
    for c,(a,b,d) in zip(st.columns(4),[
        ("Meters screened",f"{total:,}","Smart-meter records"),
        ("High risk",f"{high:,}",f"{high/total*100:.1f}% of records" if total else "—"),
        ("Medium risk",f"{med:,}",f"{med/total*100:.1f}% of records" if total else "—"),
        ("Average risk",f"{avg:.3f}","Model output")]):
        c.markdown(f'<div class="card"><div class="label">{a}</div><div class="value">{b}</div><div>{d}</div></div>',unsafe_allow_html=True)

    a,b=st.columns(2)
    counts=risk["Risk Level"].value_counts().reindex(["LOW","MEDIUM","HIGH"]).fillna(0).reset_index()
    counts.columns=["Risk Level","Meters"]
    with a:
        fig=px.bar(counts,x="Risk Level",y="Meters",text="Meters",template="plotly_dark",title="Risk classification")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)
    with b:
        fig=px.histogram(risk,x=scorec,nbins=30,template="plotly_dark",title="Risk-score distribution")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)

    st.subheader("🚨 Highest-risk meters")
    top=risk.sort_values(scorec,ascending=False).head(20)[[idc,scorec,"Risk Level"]].copy()
    top.columns=["Consumer / Meter ID","Risk Score","Risk Level"]
    st.dataframe(top,use_container_width=True,hide_index=True)
    st.markdown('<div class="note">Risk scores are screening signals for inspection prioritization, not proof of theft.</div>',unsafe_allow_html=True)

elif page=="Consumer Search":
    st.subheader("🔎 Consumer / Meter Search")
    q=st.text_input("Enter Consumer / Meter ID")
    if q:
        m=risk[risk[idc].astype(str).str.strip().str.lower()==q.strip().lower()]
        if m.empty: st.warning("Consumer / meter not found.")
        else:
            r=m.iloc[0]
            estimated="Not available"
            if did and dd:
                dm=dates[dates[did].astype(str).str.strip().str.lower()==q.strip().lower()]
                if not dm.empty: estimated=str(dm.iloc[0][dd])
            x,y,z=st.columns(3)
            x.metric("Risk score",f"{float(r[scorec]):.3f}")
            y.metric("Risk level",str(r["Risk Level"]))
            z.metric("Estimated anomaly start",estimated)
            st.markdown('<div class="note">Use this record to prioritize a physical inspection. The model result is not conclusive proof of theft.</div>',unsafe_allow_html=True)

elif page=="Inspection Queue":
    st.subheader("🚨 Inspection Queue")
    threshold=st.slider("Minimum risk score",0.0,1.0,.70,.01)
    q=risk[risk[scorec]>=threshold].sort_values(scorec,ascending=False)
    st.metric("Meters meeting threshold",f"{len(q):,}")
    view=q[[idc,scorec,"Risk Level"]].copy()
    view.columns=["Consumer / Meter ID","Risk Score","Risk Level"]
    st.dataframe(view,use_container_width=True,hide_index=True)
    st.download_button("⬇️ Download inspection queue",view.to_csv(index=False).encode(), "grid_ghost_inspection_queue.csv","text/csv")

elif page=="Timeline":
    st.subheader("📅 Anomaly Timeline")
    if dates.empty or not dd:
        st.warning("No usable theft/anomaly-date output found.")
    else:
        t=dates.copy()
        t[dd]=pd.to_datetime(t[dd],errors="coerce")
        t=t.dropna(subset=[dd])
        st.metric("Records with usable dates",f"{len(t):,}")
        if len(t):
            monthly=t.assign(Month=t[dd].dt.to_period("M").astype(str)).groupby("Month").size().reset_index(name="Meters")
            fig=px.line(monthly,x="Month",y="Meters",markers=True,template="plotly_dark",title="Estimated anomaly starts over time")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig,use_container_width=True)
        st.dataframe(t.head(500),use_container_width=True,hide_index=True)

else:
    st.subheader("About Grid Ghost")
    st.markdown('<div class="note"><b>WHO?</b> Risk score identifies meters for prioritization.<br><b>WHEN?</b> Theft/anomaly-date output estimates when suspicious behavior began.</div>',unsafe_allow_html=True)
    st.write("Files used: improved_risk_scores.csv, improved_theft_dates.csv, and optionally train.csv/meter_risk_scores.csv.")
    st.warning("Before making the GitHub repository public, confirm the hackathon data is allowed to be publicly shared.")
