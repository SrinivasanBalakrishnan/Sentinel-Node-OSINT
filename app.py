import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import graphviz
import folium
from streamlit_folium import st_folium
from datetime import datetime, timezone, timedelta
import random
import time
from fpdf import FPDF
import base64

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AVELLON | Global Risk OS",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Enterprise/Military Aesthetic
st.markdown("""
<style>
    /* Global Font & Colors */
    .stApp {
        background-color: #0e1117;
        font-family: 'Roboto Mono', monospace;
    }
    
    /* Metrics Styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700;
        color: #e0e0e0;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Custom Badges */
    .badge-critical { background-color: #ff2b2b; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    .badge-high { background-color: #ffa500; color: black; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    .badge-medium { background-color: #ffd700; color: black; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    .badge-low { background-color: #28a745; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    
    /* Chat Styling */
    .chat-row { display: flex; margin-bottom: 10px; }
    .chat-user { background-color: #2b3137; padding: 10px; border-radius: 8px; border-left: 3px solid #00d4ff; width: 80%; }
    .chat-ai { background-color: #1c2128; padding: 10px; border-radius: 8px; border-left: 3px solid #28a745; width: 80%; margin-left: auto; }
    
    /* Sidebar tightness */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. BACKEND INTELLIGENCE & DATA FUSION
# -----------------------------------------------------------------------------
if 'chat_history' not in st.session_state: st.session_state['chat_history'] = []

class SentinelBackend:
    @staticmethod
    def get_live_gmt_time():
        """Auto-corrects and returns live GMT/UTC time."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S GMT")

    @staticmethod
    def get_global_metrics():
        return {
            "risk_index": 72.4,
            "critical_events": 3,
            "escalating": 8,
            "stable_pct": 84,
            "last_refresh": SentinelBackend.get_live_gmt_time(),
            "user_role": "COMMANDER / TIER-1"
        }

    @staticmethod
    def get_map_assets():
        return [
            {"name": "Strait of Malacca", "lat": 4.2105, "lon": 101.9758, "type": "Chokepoint", "risk": "CRITICAL", "conf": 98},
            {"name": "Taiwan Strait", "lat": 23.9037, "lon": 119.6763, "type": "Chokepoint", "risk": "HIGH", "conf": 92},
            {"name": "Port of Shanghai", "lat": 31.2304, "lon": 121.4737, "type": "Port", "risk": "MEDIUM", "conf": 85},
            {"name": "Suez Canal", "lat": 30.5852, "lon": 32.3999, "type": "Chokepoint", "risk": "MEDIUM", "conf": 89},
            {"name": "Rotterdam Hub", "lat": 51.9225, "lon": 4.47917, "type": "Port", "risk": "LOW", "conf": 99},
            {"name": "Panama Canal", "lat": 9.1012, "lon": -79.6955, "type": "Chokepoint", "risk": "LOW", "conf": 95},
        ]

    @staticmethod
    def get_intelligence_feed():
        return [
            {"id": "EVT-884", "headline": "Naval Blockade Exercise Initiated", "asset": "Taiwan Strait", "category": "Conflict", "severity": "CRITICAL", "confidence": 98, "timestamp": "14m ago", "source": "SIGINT / SAT", "why": "Troop movement detected via SAR imagery."},
            {"id": "EVT-883", "headline": "Severe Cyclone Formation", "asset": "Bay of Bengal", "category": "Weather", "severity": "HIGH", "confidence": 94, "timestamp": "42m ago", "source": "NOAA / MET", "why": "Pressure drop > 20hPa."},
            {"id": "EVT-882", "headline": "Labor Strike Negotiation Stalled", "asset": "Port of LA/LB", "category": "Logistics", "severity": "MEDIUM", "confidence": 82, "timestamp": "2h ago", "source": "OSINT", "why": "Sentiment analysis negative."},
        ]

    @staticmethod
    def get_analytics_data():
        regions = ['APAC', 'EMEA', 'AMER', 'LATAM']
        risks = [45, 30, 15, 10]
        velocity = pd.DataFrame({'time': pd.date_range(start='2024-01-01', periods=10, freq='H'), 'risk_score': [20, 22, 25, 24, 30, 45, 50, 65, 72, 72]})
        root_causes = pd.DataFrame({'cause': ['Geopolitical', 'Climate', 'Cyber', 'Labor'], 'count': [40, 25, 20, 15]})
        return regions, risks, velocity, root_causes

    @staticmethod
    def get_logs():
        return pd.DataFrame([
            {"Timestamp": "10:42:01", "User": "ADMIN_01", "Action": "SIMULATION_RUN", "Target": "Taiwan_Semi"},
            {"Timestamp": "10:38:15", "User": "AUTO_BOT", "Action": "ALERT_TRIGGER", "Target": "Strait_Malacca"},
        ])

    @staticmethod
    def generate_pdf_brief():
        """Generates the downloadable Intelligence Brief."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="AVELLON INTELLIGENCE BRIEF", ln=1, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=f"Generated: {SentinelBackend.get_live_gmt_time()} | SECRET//NOFORN", ln=1, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="1. EXECUTIVE SUMMARY", ln=1, align='L')
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 10, txt="Global risk velocity has increased by 14%. Critical friction detected in the Red Sea corridor. Financial blast radius estimation for Tier-1 automotive sector is $45M/day.")
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="2. ACTIVE THREAT VECTORS", ln=1, align='L')
        pdf.set_font("Arial", size=10)
        for asset in SentinelBackend.get_map_assets():
            pdf.cell(0, 8, txt=f"- {asset['name']}: {asset['risk']} ({asset['type']})", ln=1)
        return pdf.output(dest='S').encode('latin-1')

    @staticmethod
    def ai_chat_response(query):
        """Simulates Fusion Intelligence (Outside + Inside Data)."""
        t = SentinelBackend.get_live_gmt_time()
        q = query.lower()
        if "taiwan" in q:
            return f"[{t}] **FUSION ANALYSIS:** Satellite imagery (NASA GIBS) indicates nominal naval activity. However, Dark Web chatter regarding 'silicon blockade' has spiked 300%. **PREDICTION:** Low kinetic risk, High cyber risk."
        elif "red sea" in q:
            return f"[{t}] **FUSION ANALYSIS:** Kinetic activity confirmed. **FINANCIAL IMPACT:** Rerouting costs estimated at +$1.2M per vessel. ERP correlation suggests 14-day delay for EU inventory."
        elif "malacca" in q:
            return f"[{t}] **FUSION ANALYSIS:** Strait is clear. Operational efficiency at 94%. No anomalies detected in Sentinel-2 imagery."
        else:
            return f"[{t}] **SYSTEM:** Query processed. Integrating Satellite, News, and ERP feeds... No critical anomalies found for this vector. Please specify a target asset."

# -----------------------------------------------------------------------------
# 3. COMPONENT RENDERING FUNCTIONS
# -----------------------------------------------------------------------------

def render_global_header():
    metrics = SentinelBackend.get_global_metrics()
    c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1.5, 1])
    with c1: st.metric("Global Risk Index", f"{metrics['risk_index']}", "+2.4%")
    with c2: st.metric("Active Critical", f"{metrics['critical_events']}", "Alerts")
    with c3: st.metric("Escalating", f"{metrics['escalating']}", "Assets")
    with c4: st.metric("Stable", f"{metrics['stable_pct']}%")
    with c5: st.markdown(f"**LIVE TIME (GMT)**<br><span style='color:#00d4ff'>{metrics['last_refresh']}</span>", unsafe_allow_html=True)
    with c6: st.markdown(f"**USER ROLE**<br><span style='color:#28a745'>{metrics['user_role']}</span>", unsafe_allow_html=True)
    st.markdown("---")

def render_sidebar():
    with st.sidebar:
        st.title("COMMAND CONTROL")
        st.caption(f"SYNC: {SentinelBackend.get_live_gmt_time()}")
        st.markdown("---")
        mode = st.radio("OPERATING MODE", ["🔴 LIVE MONITORING", "🔍 DEEP SCAN", "🔮 PREDICTIVE", "🎲 SIMULATION"])
        st.markdown("### FILTERS")
        st.multiselect("THREAT LEVEL", ["CRITICAL", "HIGH"], default=["CRITICAL", "HIGH"])
        st.markdown("---")
        st.info(f"System Status: ONLINE\nSatellites: CONNECTED\nLatency: 42ms")

def render_war_room_map():
    assets = SentinelBackend.get_map_assets()
    
    # Folium Map with NASA GIBS (Live Satellite Layer)
    m = folium.Map(location=[20, 80], zoom_start=2, tiles=None, height="400px")
    folium.TileLayer('CartoDB dark_matter', name="Tactical (Dark)").add_to(m)
    
    # NASA WORLDVIEW (GIBS) LAYER - LIVE DAILY IMAGERY
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    folium.TileLayer(
        tiles=f'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{today}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg',
        attr='NASA GIBS',
        name='NASA Satellite (Live)',
        overlay=True,
        control=True,
        opacity=0.6
    ).add_to(m)

    risk_colors = {"CRITICAL": "red", "HIGH": "orange", "MEDIUM": "yellow", "LOW": "green"}
    for asset in assets:
        color = risk_colors.get(asset["risk"], "grey")
        folium.CircleMarker(
            location=[asset["lat"], asset["lon"]],
            radius=8 if asset["risk"] == "CRITICAL" else 5,
            popup=f"<b>{asset['name']}</b><br>Risk: {asset['risk']}",
            color=color, fill=True, fill_color=color, fill_opacity=0.7
        ).add_to(m)
        if asset["risk"] == "CRITICAL":
            folium.Circle(location=[asset["lat"], asset["lon"]], radius=500000, color=color, weight=1, fill=True, fill_opacity=0.1).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, height=400, use_container_width=True)

def render_intelligence_feed():
    st.subheader("INTELLIGENCE STREAM")
    
    # PDF Download
    pdf_data = SentinelBackend.generate_pdf_brief()
    st.download_button("📄 Download Intelligence Brief (PDF)", data=pdf_data, file_name="Avellon_Brief.pdf", mime="application/pdf")
    
    events = SentinelBackend.get_intelligence_feed()
    for evt in events:
        badge = f"badge-{evt['severity'].lower()}"
        with st.expander(f"{evt['headline']}"):
            st.markdown(f"<span class='{badge}'>{evt['severity']}</span> <span style='color:#888'>{evt['timestamp']}</span>", unsafe_allow_html=True)
            st.write(f"**Analysis:** {evt['why']}")
            st.button("ACTION: INITIATE RESPONSE", key=evt['id'])

def render_analytics_tabs():
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 ANALYTICS", "💬 AI ANALYST", "🕸️ DIGITAL TWIN", "🎲 SIMULATION", "📜 LOGS"])
    
    # 1. Analytics
    with tab1:
        _, _, velocity_df, cause_df = SentinelBackend.get_analytics_data()
        c1, c2 = st.columns(2)
        with c1: st.altair_chart(alt.Chart(velocity_df).mark_line(color='#00d4ff').encode(x='time', y='risk_score').properties(height=200), use_container_width=True)
        with c2: st.altair_chart(alt.Chart(cause_df).mark_arc(innerRadius=50).encode(theta='count', color='cause').properties(height=200), use_container_width=True)

    # 2. AI Chatbot (New Feature)
    with tab2:
        st.markdown("#### 💬 AI RISK ANALYST (FUSION ENGINE)")
        st.caption("Fusing Satellite, Dark Web, and ERP data for predictive insights.")
        
        for msg in st.session_state['chat_history']:
            cls = "chat-user" if msg['role'] == "user" else "chat-ai"
            st.markdown(f"<div class='chat-row'><div class='{cls}'><b>{msg['role']}:</b> {msg['content']}</div></div>", unsafe_allow_html=True)
            
        q = st.chat_input("Ask about any global asset or financial impact...")
        if q:
            st.session_state['chat_history'].append({"role": "user", "content": q})
            with st.spinner("Fusing multi-INT data layers..."):
                time.sleep(1)
                resp = SentinelBackend.ai_chat_response(q)
                st.session_state['chat_history'].append({"role": "AI", "content": resp})
            st.rerun()

    # 3. Digital Twin
    with tab3:
        st.markdown("#### SUPPLY CHAIN GRAPH")
        g = graphviz.Digraph()
        g.attr(rankdir='LR', bgcolor='transparent')
        g.attr('node', shape='box', style='filled', color='white')
        g.node('A', 'Taiwan Semi', fillcolor='#ffcccc')
        g.node('B', 'Assembly', fillcolor='#ffffcc')
        g.node('C', 'Logistics', fillcolor='#ffffcc')
        g.node('D', 'Apple', fillcolor='#ccffcc')
        g.edge('A', 'B'); g.edge('B', 'C'); g.edge('C', 'D')
        st.graphviz_chart(g)

    # 4. Simulation
    with tab4:
        st.markdown("#### SCENARIO SIMULATION")
        d = st.slider("Duration (Days)", 1, 30, 7)
        st.metric("Revenue Risk", f"${d * 12.5}M", "High Confidence")
        st.progress(min(100, d*3))

    # 5. Logs
    with tab5:
        st.dataframe(SentinelBackend.get_logs(), use_container_width=True, hide_index=True)

def render_footer():
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.caption("🔒 DATA ACCESS: LEVEL 5 (TOP SECRET)")
    with c2: st.caption("🔑 API KEY: sk_live_...94x")
    with c3: st.caption("📡 SAT FEED: NASA GIBS ACTIVE")
    with c4: st.caption("🏥 HEALTH: 99.99% UPTIME")

# -----------------------------------------------------------------------------
# 4. MAIN ORCHESTRATION
# -----------------------------------------------------------------------------
def main():
    render_global_header()
    render_sidebar()
    st.markdown("### 🗺️ WAR ROOM: ACTIVE THEATER (NASA SATELLITE OVERLAY)")
    render_war_room_map()
    c_left, c_right = st.columns([1, 1.5])
    with c_left: render_intelligence_feed()
    with c_right: render_analytics_tabs()
    render_footer()

if __name__ == "__main__":
    main()
