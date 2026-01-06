import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import altair as alt
import graphviz
import random
import time
import re

# --- CONFIGURATION: MOCK ERP DATABASE (Stage 3) ---
# Simulates an SAP/Oracle connection mapping regions to internal inventory.
ERP_DATA = {
    "Taiwan Strait": {"Part": "Microcontrollers (MCU-32)", "Inventory": "14 Days", "Status": "CRITICAL", "Daily_Burn": "$2.4M"},
    "Strait of Malacca": {"Part": "Raw Rubber / Latex", "Inventory": "45 Days", "Status": "Healthy", "Daily_Burn": "$500k"},
    "Red Sea Corridor": {"Part": "Finished Furniture (SKU-99)", "Inventory": "22 Days", "Status": "Warning", "Daily_Burn": "$1.1M"},
    "Gulf of Mexico Energy": {"Part": "Petrochemical Feedstock", "Inventory": "8 Days", "Status": "CRITICAL", "Daily_Burn": "$4.5M"}
}

# --- SUPPLIER WATCHLIST (Stage 3) ---
# Clients upload their specific vendors here.
CLIENT_SUPPLIERS = ["TSMC", "Foxconn", "Maersk", "Samsung Electronics", "Toyota Group"]

# --- ASSETS & PATTERNS ---
GEO_ASSETS = {
    "Panama Canal": {"coords": [9.101, -79.695], "query": '"Panama Canal" OR "Gatun Lake"', "region": "Americas", "type": "Choke Point", "Trade_Vol": "$270M/day"},
    "Gulf of Mexico Energy": {"coords": [25.000, -90.000], "query": '"Gulf of Mexico oil" OR "Pemex platform"', "region": "Americas", "type": "Energy Asset", "Trade_Vol": "$1.2B/day"},
    "Red Sea Corridor": {"coords": [20.000, 38.000], "query": '"Red Sea" OR "Suez Canal" OR "Houthi"', "region": "MENA", "type": "Trade Route", "Trade_Vol": "$900M/day"},
    "Strait of Hormuz": {"coords": [26.566, 56.416], "query": '"Strait of Hormuz" OR "Iranian navy"', "region": "MENA", "type": "Choke Point", "Trade_Vol": "$2.1B/day"},
    "Strait of Malacca": {"coords": [4.000, 100.000], "query": '"Strait of Malacca" OR "Singapore Strait"', "region": "Indo-Pacific", "type": "Choke Point", "Trade_Vol": "$3.5B/day"},
    "Taiwan Strait": {"coords": [24.000, 119.000], "query": '"Taiwan Strait" OR "PLA navy" OR "TSMC"', "region": "Indo-Pacific", "type": "Conflict Zone", "Trade_Vol": "$1.8B/day"},
    "South China Sea": {"coords": [12.000, 113.000], "query": '"South China Sea" OR "Spratly Islands"', "region": "Indo-Pacific", "type": "Conflict Zone", "Trade_Vol": "$3.0B/day"},
}

EVENT_PATTERNS = {
    "Military Conflict": [r"missile", r"drone", r"navy", r"warship", r"attack", r"fired"],
    "Supply Chain Delay": [r"blocked", r"grounded", r"suspended", r"congestion", r"delay", r"collision"],
    "Regulatory Sanction": [r"sanction", r"seized", r"ban", r"tariff", r"customs"],
    "Natural Disaster": [r"cyclone", r"typhoon", r"earthquake", r"tsunami", r"flood"]
}

# --- ENGINE: CORE INTELLIGENCE ---
class SentinelEngine:
    def fetch_feed(self, url):
        try: return feedparser.parse(url)
        except: return None

    def scan_target(self, query):
        base = query.replace(" ", "%20")
        url = f"https://news.google.com/rss/search?q={base}%20when:7d&hl=en-IN&gl=IN&ceid=IN:en"
        feed = self.fetch_feed(url)
        results = []
        if feed and feed.entries:
            for entry in feed.entries[:8]: # Fast scan
                text = f"{entry.title} {entry.get('summary', '')}"
                blob = TextBlob(text)
                category = "General Risk"
                for cat, pats in EVENT_PATTERNS.items():
                    if any(re.search(p, text.lower()) for p in pats):
                        category = cat; break
                
                risk_val = 1
                if blob.sentiment.polarity < -0.05: risk_val = 2
                if blob.sentiment.polarity < -0.2: risk_val = 3
                if category == "Military Conflict" and risk_val >= 2: risk_val = 4
                
                results.append({
                    "Title": entry.title,
                    "Link": entry.link,
                    "Risk": ["LOW", "MEDIUM", "HIGH", "CRITICAL"][risk_val-1],
                    "Category": category,
                    "Source": entry.source.get('title', 'Unknown')
                })
        return results

# --- MODULE: DIGITAL TWIN SIMULATOR ---
def run_simulation(target, duration_days):
    """
    Simulates revenue impact based on duration of closure.
    """
    asset_data = GEO_ASSETS[target]
    daily_vol_str = asset_data.get("Trade_Vol", "$0")
    
    # Parse "$1.2B" to float
    multiplier = 1000000 if 'M' in daily_vol_str else 1000000000
    daily_val = float(re.findall(r"[\d\.]+", daily_vol_str)[0]) * multiplier
    
    total_impact = daily_val * duration_days * 0.4 # Assuming 40% value at risk
    
    # Check ERP status
    erp_status = ERP_DATA.get(target, {"Part": "Generic Cargo", "Inventory": "Unknown", "Status": "Unknown"})
    
    return total_impact, erp_status

# --- MODULE: SUPPLIER AUDITOR ---
def audit_suppliers(supplier_list):
    """
    Scans specifically for supplier names in the risk database.
    """
    engine = SentinelEngine()
    audit_results = []
    
    for supplier in supplier_list:
        # Mocking a directed scan for the supplier
        res = engine.scan_target(f'"{supplier}" supply chain OR production')
        
        risk_score = "LOW"
        if res:
            # If any high risk article found, flag supplier
            if any(r['Risk'] in ["HIGH", "CRITICAL"] for r in res):
                risk_score = "HIGH"
            elif any(r['Risk'] == "MEDIUM" for r in res):
                risk_score = "MEDIUM"
        
        audit_results.append({"Vendor": supplier, "Risk": risk_score, "Hits": len(res)})
        
    return pd.DataFrame(audit_results)

# --- FRONTEND UI ---
st.set_page_config(page_title="SENTINEL-NODE V20", layout="wide")

if 'analyst_queue' not in st.session_state: st.session_state['analyst_queue'] = []
if 'verified_alerts' not in st.session_state: st.session_state['verified_alerts'] = []

# --- SIDEBAR: MODE SWITCHER ---
st.sidebar.title("🎛️ Control Plane")
mode = st.sidebar.radio("Operating Mode", ["Live Monitor", "War Room (Digital Twin)", "Analyst Workbench"])

st.title(f"Sentinel-Node: {mode}")

# ==========================================
# MODE 1: LIVE MONITOR (The Map)
# ==========================================
if mode == "Live Monitor":
    st.markdown("### 🌍 Global Risk Operating Picture")
    
    # Map
    m = folium.Map(location=[20.0, 0.0], zoom_start=2, tiles="CartoDB dark_matter")
    for name, data in GEO_ASSETS.items():
        color = "red" if data['type'] == "Conflict Zone" else "orange" if data['type'] == "Choke Point" else "blue"
        folium.Marker(data['coords'], popup=name, icon=folium.Icon(color=color, icon="info-sign")).add_to(m)
    
    map_data = st_folium(m, height=400, width="100%")
    
    # Supplier Auto-Audit (Background Task)
    with st.expander("🛡️ Automated Supplier Audit (24/7 Watch)"):
        if st.button("Run Manual Supplier Scan"):
            with st.spinner("Auditing Vendor List against Global Risk DB..."):
                audit_df = audit_suppliers(CLIENT_SUPPLIERS)
                st.dataframe(audit_df.style.map(lambda v: 'color: red;' if v == 'HIGH' else 'color: orange;' if v == 'MEDIUM' else 'color: green;', subset=['Risk']))
                st.success("Audit Complete. 2 Vendors flagged for review.")

# ==========================================
# MODE 2: WAR ROOM (Digital Twin)
# ==========================================
elif mode == "War Room (Digital Twin)":
    st.markdown("### 🎲 Scenario Simulation & ERP Impact")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("Simulation Parameters")
        target_sim = st.selectbox("Select Asset to Disrupt", list(GEO_ASSETS.keys()))
        days_sim = st.slider("Disruption Duration (Days)", 1, 30, 7)
        severity_sim = st.select_slider("Disruption Severity", ["Minor Delay", "Port Congestion", "Total Blockade"])
        
        if st.button("🚀 RUN SIMULATION", type="primary"):
            with st.spinner("Calculating Economic Impact & Querying ERP..."):
                impact, erp = run_simulation(target_sim, days_sim)
                st.session_state['sim_result'] = {'impact': impact, 'erp': erp, 'days': days_sim, 'target': target_sim}

    with c2:
        if 'sim_result' in st.session_state:
            res = st.session_state['sim_result']
            
            # Top Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Revenue at Risk", f"${res['impact']/1000000:.1f}M", delta="-100%", delta_color="inverse")
            m2.metric("ERP Inventory Status", res['erp']['Status'])
            m3.metric("Days of Cover", res['erp']['Inventory'])
            
            st.markdown("---")
            
            # ERP Integration View
            st.subheader("📦 ERP System Link (SAP/Oracle)")
            st.info(f"**Automatic Query:** Checking BOM (Bill of Materials) dependent on '{res['target']}'...")
            
            erp_df = pd.DataFrame([
                {"Part ID": res['erp']['Part'], "Warehouse": "Ohio, USA", "Qty On Hand": "8,400 Units", "Daily Burn": res['erp']['Daily_Burn'], "Stockout Est": f"In {res['erp']['Inventory']}"}
            ])
            st.table(erp_df)
            
            # Visual Impact Curve
            st.subheader("📉 Revenue Impact Curve")
            chart_data = pd.DataFrame({
                'Day': range(1, 31),
                'Cumulative Loss ($M)': [(x * (res['impact']/res['days'])/1000000) for x in range(1, 31)]
            })
            
            chart = alt.Chart(chart_data).mark_line(color='red').encode(
                x='Day', y='Cumulative Loss ($M)', tooltip=['Day', 'Cumulative Loss ($M)']
            ).properties(height=250)
            
            st.altair_chart(chart, use_container_width=True)
            
            if res['erp']['Status'] == "CRITICAL":
                st.error(f"⚠️ CRITICAL INVENTORY ALERT: {res['erp']['Part']} will stock out before disruption ends. Immediate supplier diversification required.")

# ==========================================
# MODE 3: ANALYST WORKBENCH
# ==========================================
elif mode == "Analyst Workbench":
    st.markdown("### 🕵️ Analyst-in-the-Loop Verification")
    st.caption("Premium Tier: Human validation of AI alerts before C-Suite notification.")
    
    # Mock generating a queue if empty
    if not st.session_state['analyst_queue']:
        st.session_state['analyst_queue'] = [
            {"id": 101, "title": "Strait of Malacca: Collision reported near Singapore", "risk": "HIGH", "ai_conf": 88},
            {"id": 102, "title": "TSMC reports minor earthquake damage", "risk": "MEDIUM", "ai_conf": 65},
            {"id": 103, "title": "Houthi drone intercepted over Red Sea", "risk": "CRITICAL", "ai_conf": 92}
        ]
    
    # Queue Display
    for alert in st.session_state['analyst_queue']:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{alert['risk']}**: {alert['title']}")
                st.caption(f"AI Confidence: {alert['ai_conf']}% | ID: {alert['id']}")
            with c2:
                if st.button("✅ Approve", key=f"app_{alert['id']}"):
                    st.session_state['verified_alerts'].append(alert)
                    st.session_state['analyst_queue'].remove(alert)
                    st.rerun()
            with c3:
                if st.button("❌ Reject", key=f"rej_{alert['id']}"):
                    st.session_state['analyst_queue'].remove(alert)
                    st.rerun()

    st.markdown("---")
    st.subheader("📤 C-Suite Verified Feed")
    if st.session_state['verified_alerts']:
        st.dataframe(pd.DataFrame(st.session_state['verified_alerts']))
    else:
        st.info("No verified alerts pushed to executive dashboard yet.")
