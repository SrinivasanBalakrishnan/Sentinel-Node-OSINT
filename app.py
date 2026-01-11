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
import uuid

# -----------------------------------------------------------------------------
# 1. ENTERPRISE CONFIGURATION & SESSION STATE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AVELLON | Global Risk OS",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if 'system_state' not in st.session_state:
    st.session_state['system_state'] = {
        'risk_index': 72.4,
        'risk_history': [70, 71, 72, 72.4],
        'active_alerts': 3,
        'chat_history': [],
        'last_update': datetime.now(timezone.utc)
    }
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# -----------------------------------------------------------------------------
# 2. STYLING (PHASE 2 HUD + GLOBAL STYLES)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    :root {
        --bg-color: #0d1117;
        --card-bg: #161b22;
        --surface-hover: #1f2937;
        --border-color: #30363d;
        --accent-primary: #58a6ff;
        --accent-danger: #f85149;
        --accent-warning: #d29922;
        --accent-success: #3fb950;
        --text-primary: #f0f6fc;
        --text-secondary: #8b949e;
        --font-mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    }

    .stApp {
        background-color: var(--bg-color);
        color: var(--text-primary);
        font-family: 'Segoe UI', system-ui, sans-serif;
    }

    /* HUD Header Styling */
    .hud-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 15px;
        background: linear-gradient(180deg, rgba(22,27,34,0.6) 0%, rgba(13,17,23,0) 100%);
    }
    .hud-title-section { display: flex; align-items: center; gap: 15px; }
    .hud-logo { font-size: 28px; }
    .hud-text-group { display: flex; flex-direction: column; }
    .hud-main-title { font-weight: 700; font-size: 20px; letter-spacing: 1.2px; color: var(--text-primary); }
    .hud-subtitle { font-size: 11px; color: var(--text-secondary); font-family: var(--font-mono); display: flex; align-items: center; gap: 6px; }

    /* Live Pulse Animation */
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(248, 81, 73, 0.7); }
        70% { box-shadow: 0 0 0 6px rgba(248, 81, 73, 0); }
        100% { box-shadow: 0 0 0 0 rgba(248, 81, 73, 0); }
    }
    .status-dot {
        height: 8px; width: 8px; background-color: var(--accent-danger);
        border-radius: 50%; display: inline-block; animation: pulse-red 2s infinite;
    }

    /* Metric Group Styling */
    .hud-metrics { display: flex; gap: 40px; align-items: center; }
    .hud-metric-box { text-align: right; }
    .hud-metric-label { font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
    .hud-metric-value { font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 24px; font-weight: 600; margin-top: 2px; }

    /* Badges */
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; display: inline-block; font-family: var(--font-mono); }
    .badge-critical { background: rgba(248, 81, 73, 0.2); color: var(--accent-danger); border: 1px solid var(--accent-danger); }
    .badge-high { background: rgba(210, 153, 34, 0.2); color: var(--accent-warning); border: 1px solid var(--accent-warning); }
    .badge-medium { background: rgba(88, 166, 255, 0.2); color: var(--accent-primary); border: 1px solid var(--accent-primary); }
    .badge-low { background: rgba(63, 185, 80, 0.2); color: var(--accent-success); border: 1px solid var(--accent-success); }
    
    .block-container { padding-top: 1.5rem; }
    hr { border-color: var(--border-color) !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. BACKEND (DYNAMIC SIMULATION)
# -----------------------------------------------------------------------------
class EnterpriseBackend:
    @staticmethod
    def get_system_time():
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S GMT")

    @staticmethod
    def get_global_metrics():
        # Dynamic Simulation
        current_risk = st.session_state['system_state']['risk_index']
        drift = np.random.uniform(-0.5, 0.8)
        new_risk = max(0, min(100, current_risk + drift))
        
        st.session_state['system_state']['risk_index'] = new_risk
        st.session_state['system_state']['risk_history'].append(new_risk)
        if len(st.session_state['system_state']['risk_history']) > 24:
            st.session_state['system_state']['risk_history'].pop(0)

        return {
            "risk_index": f"{new_risk:.2f}",
            "risk_delta": f"{drift:+.2f}%",
            "critical_events": st.session_state['system_state']['active_alerts'],
            "escalating": 8,
            "stable_pct": 84,
            "last_refresh": EnterpriseBackend.get_system_time(),
            "user_role": "COMMANDER / TIER-1",
            "latency": f"{np.random.randint(18, 42)}ms"
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
        history = st.session_state['system_state']['risk_history']
        times = [datetime.now() - timedelta(hours=i) for i in range(len(history))][::-1]
        velocity = pd.DataFrame({'time': times, 'risk_score': history})
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
        pdf.cell(200, 10, txt=f"Generated: {EnterpriseBackend.get_system_time()} | SECRET//NOFORN", ln=1, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="1. EXECUTIVE SUMMARY", ln=1, align='L')
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 10, txt="Global risk velocity has increased. Critical friction detected in the Red Sea corridor. Financial blast radius estimation for Tier-1 automotive sector is significant.")
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="2. ACTIVE THREAT VECTORS", ln=1, align='L')
        pdf.set_font("Arial", size=10)
        for asset in EnterpriseBackend.get_map_assets():
            pdf.cell(0, 8, txt=f"- {asset['name']}: {asset['risk']} ({asset['type']})", ln=1)
        return pdf.output(dest='S').encode('latin-1')

    @staticmethod
    def ai_chat_response(query):
        t = EnterpriseBackend.get_system_time()
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
# 4. RENDER FUNCTIONS (HUD + MAP + UI)
# -----------------------------------------------------------------------------

def render_enterprise_header():
    """Renders the Phase 2 Professional HUD Header."""
    metrics = EnterpriseBackend.get_global_metrics()
    
    st.markdown(f"""
    <div class="hud-container">
        <div class="hud-title-section">
            <div class="hud-logo">🛡️</div>
            <div class="hud-text-group">
                <div class="hud-main-title">AVELLON | OS</div>
                <div class="hud-subtitle">
                    <span class="status-dot"></span>
                    LIVE FEED • {metrics['last_refresh']}
                </div>
            </div>
        </div>
        
        <div class="hud-metrics">
            <div class="hud-metric-box">
                <div class="hud-metric-label">Global Risk Index</div>
                <div class="hud-metric-value" style="color: {'var(--accent-danger)' if float(metrics['risk_index']) > 70 else 'var(--accent-primary)'}">
                    {metrics['risk_index']} <span style="font-size:14px; color:var(--text-secondary)">{metrics['risk_delta']}</span>
                </div>
            </div>
            <div class="hud-metric-box">
                <div class="hud-metric-label">Active Alerts</div>
                <div class="hud-metric-value" style="color: var(--accent-warning)">{metrics['critical_events']}</div>
            </div>
            <div class="hud-metric-box">
                <div class="hud-metric-label">System Latency</div>
                <div class="hud-metric-value" style="color: var(--accent-success)">{metrics['latency']}</div>
            </div>
            <div class="hud-metric-box">
                <div class="hud-metric-label">Role</div>
                <div class="hud-metric-value" style="font-size: 16px; color: var(--text-primary); margin-top:8px;">{metrics['user_role']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.caption(f"COMMAND TOOLS")
        st.markdown("---")
        st.radio("MODE", ["LIVE MONITORING", "DEEP SCAN", "SIMULATION"], label_visibility="collapsed")
        
        st.markdown("### FILTERS")
        st.multiselect("THREAT LEVEL", ["CRITICAL", "HIGH", "MEDIUM", "LOW"], default=["CRITICAL", "HIGH"])
        
        st.markdown("---")
        st.checkbox("Show Weather Layers", value=True)
        st.checkbox("Show Naval Assets", value=False)
        st.markdown("---")
        st.info("System Status: **ONLINE**")

def render_map_section():
    st.markdown("### 🗺️ GLOBAL THEATER OVERVIEW")
    m = folium.Map(location=[20, 80], zoom_start=2, tiles=None)
    folium.TileLayer('CartoDB dark_matter', name="Dark").add_to(m)
    
    # NASA GIBS
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    folium.TileLayer(
        tiles=f'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{today}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg',
        attr='NASA GIBS', overlay=True, opacity=0.5
    ).add_to(m)

    for a in EnterpriseBackend.get_map_assets():
        c = {"CRITICAL": "#f85149", "HIGH": "#d29922", "MEDIUM": "#58a6ff", "LOW": "#3fb950"}.get(a['risk'])
        
        # HTML Tooltip
        tooltip = f"""
        <div style='font-family:sans-serif; padding:5px;'>
            <b>{a['name']}</b><br>
            <span style='color:{c}'>● {a['risk']}</span><br>
            <span style='font-size:10px; color:#666'>{a['type']}</span>
        </div>
        """
        
        folium.CircleMarker([a['lat'], a['lon']], radius=6, color=c, fill=True, fill_opacity=0.9, popup=tooltip, tooltip=a['name']).add_to(m)
        if a['risk'] == "CRITICAL":
            folium.Circle([a['lat'], a['lon']], radius=500000, color=c, weight=1, fill=True, fill_opacity=0.1).add_to(m)
            
    st_folium(m, height=420, use_container_width=True)

# -----------------------------------------------------------------------------
# 5. MAIN EXECUTION
# -----------------------------------------------------------------------------
def main():
    # 1. Render Professional HUD Header
    render_enterprise_header()
    render_sidebar()
    
    # Layout
    c_map, c_feed = st.columns([2, 1])
    
    with c_map:
        render_map_section()
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ANALYTICS TABS (Restored all tabs)
        t1, t2, t3, t4 = st.tabs(["📊 ANALYTICS", "💬 AI ANALYST", "🕸️ DIGITAL TWIN", "🎲 SIMULATION"])
        
        with t1:
            vel_df, cause_df = EnterpriseBackend.get_analytics_data()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Risk Velocity (Live Feed)**")
                st.altair_chart(alt.Chart(vel_df).mark_area(
                    line={'color':'#58a6ff'},
                    color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#58a6ff', offset=0), alt.GradientStop(color='rgba(88,166,255,0)', offset=1)], x1=1, x2=1, y1=1, y2=0)
                ).encode(x='time', y='risk_score').properties(height=220), use_container_width=True)
            with c2:
                st.markdown("**Root Cause Analysis**")
                st.altair_chart(alt.Chart(cause_df).mark_arc(innerRadius=50).encode(theta='count', color='cause').properties(height=220), use_container_width=True)
                
        with t2:
            st.markdown("#### 💬 AI FUSION ANALYST (Multi-INT)")
            # Chat Interface
            cnt = st.container(height=300)
            with cnt:
                for msg in st.session_state['chat_history']:
                    st.chat_message(msg['role']).write(msg['content'])
            
            q = st.chat_input("Ask about global assets, financial impact, or weather patterns...")
            if q:
                st.session_state['chat_history'].append({"role": "user", "content": q})
                with st.spinner("Processing intelligence streams..."):
                    time.sleep(0.8) 
                    resp = EnterpriseBackend.ai_chat_response(q)
                    st.session_state['chat_history'].append({"role": "assistant", "content": resp})
                st.rerun()

        with t3:
            st.markdown("#### SUPPLY CHAIN DIGITAL TWIN")
            # 
            g = graphviz.Digraph()
            g.attr(rankdir='LR', bgcolor='transparent')
            g.attr('node', shape='box', style='filled', color='white', fontname='Sans-Serif')
            g.node('A', 'Taiwan Semi', fillcolor='#4a1c1c', fontcolor='white') 
            g.node('B', 'Assembly Node', fillcolor='#3a2e1c', fontcolor='white') 
            g.node('C', 'Global Logistics', fillcolor='#1c3a2e', fontcolor='white')
            g.node('D', 'End Market', fillcolor='#1c2e4a', fontcolor='white')
            g.edge('A', 'B'); g.edge('B', 'C'); g.edge('C', 'D')
            st.graphviz_chart(g, use_container_width=True)

        with t4:
            st.markdown("#### SCENARIO SIMULATOR")
            d = st.slider("Disruption Duration (Days)", 1, 60, 7)
            impact = d * 12.5
            st.metric("Estimated Revenue Impact", f"${impact:,.1f}M", "High Confidence")
            st.progress(min(100, d*2))
            
    with c_feed:
        st.subheader("📡 INTEL FEED")
        
        # PDF Button
        pdf_bytes = EnterpriseBackend.generate_pdf_brief()
        st.download_button("📄 Download Brief (PDF)", data=pdf_bytes, file_name="Avellon_Brief.pdf", mime="application/pdf", use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)

        for i in EnterpriseBackend.get_intelligence_feed():
            b_cls = f"badge badge-{i['severity'].lower()}"
            with st.expander(f"{i['headline']}"):
                st.markdown(f"<span class='{b_cls}'>{i['severity']}</span> {i['timestamp']}", unsafe_allow_html=True)
                st.caption(f"Source: {i['source']}")
                st.write(i['why'])
        
        st.markdown("---")
        st.markdown("**SYSTEM LOGS**")
        st.dataframe(EnterpriseBackend.get_logs(), use_container_width=True, hide_index=True)

    # Footer
    st.markdown("---")
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1: st.caption("🔒 DATA ACCESS: LEVEL 5 (TOP SECRET)")
    with fc2: st.caption("🔑 API KEY: sk_live_...94x")
    with fc3: st.caption("📡 SAT FEED: NASA GIBS ACTIVE")
    with fc4: st.caption("🏥 HEALTH: 99.99% UPTIME")

if __name__ == "__main__":
    main()
