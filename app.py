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

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AVELLON | Global Risk OS",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Dark Theme CSS with Enterprise Aesthetic
st.markdown("""
<style>
    :root {
        --bg: #0d1117;
        --surface: #161b22;
        --surface-hover: #1f2937;
        --text-primary: #e6edf3;
        --text-secondary: #8b949e;
        --accent: #58a6ff;
        --critical: #f85149;
        --high: #f0883e;
        --medium: #d2a241;
        --low: #3fb950;
        --border: #30363d;
    }

    /* Global App Styling */
    .stApp {
        background-color: var(--bg);
        color: var(--text-primary);
        font-family: 'Segoe UI', 'Roboto Mono', system-ui, sans-serif;
    }

    /* Custom Card Containers */
    .card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Metric Cards */
    .metric-card {
        background: var(--surface);
        border-left: 4px solid var(--accent);
        border-radius: 6px;
        padding: 1rem;
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        background: var(--surface-hover);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--text-secondary);
        margin-top: 0.5rem;
    }

    /* Badges */
    .badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        display: inline-block;
    }
    .badge-critical { background: var(--critical); color: #fff; }
    .badge-high { background: var(--high); color: #000; }
    .badge-medium { background: var(--medium); color: #000; }
    .badge-low { background: var(--low); color: #fff; }

    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. BACKEND INTELLIGENCE (MOCK API)
# -----------------------------------------------------------------------------
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

class SentinelBackend:
    @staticmethod
    def get_live_gmt_time():
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
        #  - Conceptual reference for asset placement
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
        velocity = pd.DataFrame({
            'time': pd.date_range(start='2024-01-01', periods=10, freq='H'),
            'risk_score': [20, 22, 25, 24, 30, 45, 50, 65, 72, 72]
        })
        root_causes = pd.DataFrame({'cause': ['Geopolitical', 'Climate', 'Cyber', 'Labor'], 'count': [40, 25, 20, 15]})
        return velocity, root_causes

    @staticmethod
    def get_logs():
        return pd.DataFrame([
            {"Timestamp": "10:42:01", "User": "ADMIN_01", "Action": "SIMULATION_RUN", "Target": "Taiwan_Semi"},
            {"Timestamp": "10:38:15", "User": "AUTO_BOT", "Action": "ALERT_TRIGGER", "Target": "Strait_Malacca"},
            {"Timestamp": "10:35:22", "User": "SYS_CORE", "Action": "DATA_SYNC", "Target": "Global_Node"},
        ])

    @staticmethod
    def generate_pdf_brief():
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
# 3. UI COMPONENTS
# -----------------------------------------------------------------------------

def render_metric_card(label, value, delta=None, border_color="var(--accent)"):
    delta_html = f"<div style='color:{border_color}; font-size:0.85rem; margin-top:4px;'>{delta}</div>" if delta else ""
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: {border_color};">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def render_header():
    m = SentinelBackend.get_global_metrics()
    c1, c2, c3, c4, c5, c6 = st.columns([1,1,1,1,1.5,1.2])
    
    with c1: render_metric_card("RISK INDEX", m['risk_index'], "+2.4%", "var(--critical)")
    with c2: render_metric_card("CRITICAL", m['critical_events'], "Active Alerts", "var(--critical)")
    with c3: render_metric_card("ESCALATING", m['escalating'], "Assets", "var(--high)")
    with c4: render_metric_card("STABLE", f"{m['stable_pct']}%", None, "var(--low)")
    
    with c5:
        st.markdown(f"""
        <div class="card" style="text-align:center; padding:0.8rem;">
            <div style="color:var(--text-secondary); font-size:0.7rem; letter-spacing:1px;">LIVE TIME (GMT)</div>
            <div style="color:var(--accent); font-size:1.2rem; font-weight:bold;">{m['last_refresh']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c6:
         st.markdown(f"""
        <div class="card" style="text-align:center; padding:0.8rem;">
            <div style="color:var(--text-secondary); font-size:0.7rem; letter-spacing:1px;">USER ROLE</div>
            <div style="color:var(--low); font-size:1.1rem; font-weight:bold;">{m['user_role']}</div>
        </div>
        """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.title("🛡️ AVELLON")
        st.caption(f"Command Control • {SentinelBackend.get_live_gmt_time()}")
        st.markdown("---")
        
        st.subheader("OPERATING MODE")
        st.radio("Select Mode", ["🔴 LIVE MONITORING", "🔍 DEEP SCAN", "🔮 PREDICTIVE", "🎲 SIMULATION"], label_visibility="collapsed")
        
        st.markdown("### FILTERS")
        st.multiselect("Threat Level", ["CRITICAL", "HIGH", "MEDIUM", "LOW"], default=["CRITICAL", "HIGH"])
        
        st.markdown("---")
        st.info("System Status: **ONLINE**\nSatellites: **CONNECTED**\nLatency: **42ms**")

def render_map_section():
    st.markdown("### 🗺️ WAR ROOM – Live Theater (NASA GIBS Overlay)")
    assets = SentinelBackend.get_map_assets()
    
    # Base Map
    m = folium.Map(location=[20, 80], zoom_start=2, tiles=None)
    folium.TileLayer('CartoDB dark_matter', name="Tactical Dark").add_to(m)

    # NASA GIBS Layer (Live Satellite Imagery)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    folium.TileLayer(
        tiles=f'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{today}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg',
        attr='NASA GIBS',
        name='NASA Satellite (Live)',
        overlay=True,
        opacity=0.6
    ).add_to(m)

    # Plot Assets
    risk_colors = {"CRITICAL": "red", "HIGH": "orange", "MEDIUM": "#d2a241", "LOW": "green"}
    for asset in assets:
        c = risk_colors.get(asset["risk"], "grey")
        folium.CircleMarker(
            location=[asset["lat"], asset["lon"]],
            radius=9 if asset["risk"] == "CRITICAL" else 6,
            popup=f"<b>{asset['name']}</b><br>Risk: {asset['risk']}",
            color=c, fill=True, fill_color=c, fill_opacity=0.8
        ).add_to(m)
        
        if asset["risk"] == "CRITICAL":
            folium.Circle(location=[asset["lat"], asset["lon"]], radius=500000, color=c, weight=1, fill=True, fill_opacity=0.15).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, height=450, use_container_width=True)

# -----------------------------------------------------------------------------
# 4. MAIN LAYOUT ORCHESTRATION
# -----------------------------------------------------------------------------
def main():
    render_header()
    render_sidebar()
    
    st.markdown("---")
    
    # Split layout: Map (Left 65%) | Intelligence Feed (Right 35%)
    c_map, c_feed = st.columns([2, 1])
    
    with c_map:
        render_map_section()
        
        # Tabs below Map
        st.markdown("<br>", unsafe_allow_html=True)
        tab1, tab2, tab3, tab4 = st.tabs(["📊 ANALYTICS", "💬 AI FUSION ANALYST", "🕸️ DIGITAL TWIN", "🎲 SIMULATION"])
        
        with tab1:
            vel_df, cause_df = SentinelBackend.get_analytics_data()
            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown("**Risk Velocity (Last 12H)**")
                st.altair_chart(alt.Chart(vel_df).mark_line(color='#58a6ff', point=True).encode(x='time', y='risk_score').properties(height=220), use_container_width=True)
            with cc2:
                st.markdown("**Root Cause Analysis**")
                st.altair_chart(alt.Chart(cause_df).mark_arc(innerRadius=50).encode(theta='count', color='cause').properties(height=220), use_container_width=True)

        with tab2:
            st.markdown("#### 💬 AI FUSION ANALYST (Multi-INT)")
            st.caption("Fusing Satellite, Dark Web, and ERP data layers.")
            
            # Chat Interface
            cnt = st.container(height=300)
            with cnt:
                for msg in st.session_state['chat_history']:
                    st.chat_message(msg['role']).write(msg['content'])
            
            q = st.chat_input("Ask about global assets, financial impact, or weather patterns...")
            if q:
                st.session_state['chat_history'].append({"role": "user", "content": q})
                with st.spinner("Processing intelligence streams..."):
                    time.sleep(1) # Simulation delay
                    resp = SentinelBackend.ai_chat_response(q)
                    st.session_state['chat_history'].append({"role": "assistant", "content": resp})
                st.rerun()

        with tab3:
            st.markdown("#### SUPPLY CHAIN DIGITAL TWIN")
            #  - Graphviz generated
            g = graphviz.Digraph()
            g.attr(rankdir='LR', bgcolor='transparent')
            g.attr('node', shape='box', style='filled', color='white', fontname='Sans-Serif')
            g.node('A', 'Taiwan Semi', fillcolor='#4a1c1c', fontcolor='white') # Critical
            g.node('B', 'Assembly Node', fillcolor='#3a2e1c', fontcolor='white') # Warning
            g.node('C', 'Global Logistics', fillcolor='#1c3a2e', fontcolor='white') # Safe
            g.node('D', 'End Market', fillcolor='#1c2e4a', fontcolor='white')
            g.edge('A', 'B'); g.edge('B', 'C'); g.edge('C', 'D')
            st.graphviz_chart(g, use_container_width=True)

        with tab4:
            st.markdown("#### SCENARIO SIMULATOR")
            d = st.slider("Disruption Duration (Days)", 1, 60, 7)
            impact = d * 12.5
            st.metric("Estimated Revenue Impact", f"${impact:,.1f}M", "High Confidence")
            st.progress(min(100, d*2))
            
    with c_feed:
        st.subheader("📡 INTELLIGENCE STREAM")
        
        # PDF Button
        pdf_bytes = SentinelBackend.generate_pdf_brief()
        st.download_button("📄 Download Brief (PDF)", data=pdf_bytes, file_name="Avellon_Brief.pdf", mime="application/pdf", use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Feed Items
        feed = SentinelBackend.get_intelligence_feed()
        for item in feed:
            badge_class = f"badge badge-{item['severity'].lower()}"
            with st.expander(f"{item['headline']}"):
                st.markdown(f"<span class='{badge_class}'>{item['severity']}</span> &nbsp; <span style='color:#888'>{item['timestamp']}</span>", unsafe_allow_html=True)
                st.caption(f"Source: {item['source']}")
                st.write(f"**Analysis:** {item['why']}")
                if st.button("ACTIVATE PROTOCOL", key=item['id']):
                    st.toast(f"Protocol initiated for {item['id']}", icon="⚡")
        
        st.markdown("---")
        st.markdown("**SYSTEM LOGS**")
        st.dataframe(SentinelBackend.get_logs(), use_container_width=True, hide_index=True)

    # Footer
    st.markdown("---")
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1: st.caption("🔒 DATA ACCESS: LEVEL 5 (TOP SECRET)")
    with fc2: st.caption("🔑 API KEY: sk_live_...94x")
    with fc3: st.caption("📡 SAT FEED: NASA GIBS ACTIVE")
    with fc4: st.caption("🏥 HEALTH: 99.99% UPTIME")

if __name__ == "__main__":
    main()
