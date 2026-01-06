import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import graphviz
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import random

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SENTINEL-NODE | Global Risk OS",
    page_icon="📡",
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
    
    /* Section Headers */
    h1, h2, h3 {
        color: #f0f2f6;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    /* Card/Feed Styling */
    .feed-card {
        background-color: #1c2128;
        border-left: 4px solid #444;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 0 4px 4px 0;
    }
    .feed-card:hover {
        border-left-color: #00d4ff;
        background-color: #262c36;
    }
    
    /* Sidebar tightness */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. MOCK BACKEND INTELLIGENCE (SIMULATION LAYER)
# -----------------------------------------------------------------------------
class SentinelBackend:
    @staticmethod
    def get_global_metrics():
        return {
            "risk_index": 72.4,
            "critical_events": 3,
            "escalating": 8,
            "stable_pct": 84,
            "last_refresh": datetime.now().strftime("%H:%M:%S UTC"),
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
            {
                "id": "EVT-2024-884",
                "headline": "Naval Blockade Exercise Initiated",
                "asset": "Taiwan Strait",
                "category": "Conflict",
                "severity": "CRITICAL",
                "confidence": 98,
                "timestamp": "T-minus 14m",
                "source": "SIGINT / SAT",
                "why": "Troop movement detected via SAR imagery; matched adversarial pattern #442."
            },
            {
                "id": "EVT-2024-883",
                "headline": "Severe Cyclone Formation",
                "asset": "Bay of Bengal",
                "category": "Weather",
                "severity": "HIGH",
                "confidence": 94,
                "timestamp": "T-minus 42m",
                "source": "NOAA / MET",
                "why": "Pressure drop > 20hPa in 6 hours. Impact probable for Chennai port."
            },
            {
                "id": "EVT-2024-882",
                "headline": "Labor Strike Negotiation Stalled",
                "asset": "Port of LA/LB",
                "category": "Logistics",
                "severity": "MEDIUM",
                "confidence": 82,
                "timestamp": "T-minus 2h",
                "source": "OSINT / NEWS",
                "why": "Union rep statement sentiment analysis negative (-0.8)."
            },
            {
                "id": "EVT-2024-881",
                "headline": "New Sanctions Protocol Active",
                "asset": "Global",
                "category": "Regulatory",
                "severity": "LOW",
                "confidence": 100,
                "timestamp": "T-minus 5h",
                "source": "GOV / FEED",
                "why": "Official treasury release parsed."
            }
        ]

    @staticmethod
    def get_analytics_data():
        # Mock data for Altair charts
        regions = ['APAC', 'EMEA', 'AMER', 'LATAM']
        risks = [45, 30, 15, 10]
        velocity = pd.DataFrame({
            'time': pd.date_range(start='2024-01-01', periods=10, freq='H'),
            'risk_score': [20, 22, 25, 24, 30, 45, 50, 65, 72, 72]
        })
        root_causes = pd.DataFrame({
            'cause': ['Geopolitical', 'Climate', 'Cyber', 'Labor'],
            'count': [40, 25, 20, 15]
        })
        return regions, risks, velocity, root_causes

    @staticmethod
    def get_logs():
        return pd.DataFrame([
            {"Timestamp": "10:42:01", "User": "ADMIN_01", "Action": "SIMULATION_RUN", "Target": "Taiwan_Semi"},
            {"Timestamp": "10:38:15", "User": "AUTO_BOT", "Action": "ALERT_TRIGGER", "Target": "Strait_Malacca"},
            {"Timestamp": "10:15:22", "User": "ANALYST_K", "Action": "CONFIDENCE_OVERRIDE", "Target": "EVT-882"},
        ])

# -----------------------------------------------------------------------------
# 3. COMPONENT RENDERING FUNCTIONS
# -----------------------------------------------------------------------------

def render_global_header():
    metrics = SentinelBackend.get_global_metrics()
    
    # Top Bar Layout
    c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1.5, 1])
    
    with c1:
        st.metric("Global Risk Index", f"{metrics['risk_index']}", "+2.4%")
    with c2:
        st.metric("Active Critical", f"{metrics['critical_events']}", "Alerts")
    with c3:
        st.metric("Escalating Risks", f"{metrics['escalating']}", "Assets")
    with c4:
        st.metric("Stable Assets", f"{metrics['stable_pct']}%")
    with c5:
        st.markdown(f"**LAST REFRESH**<br><span style='color:#00d4ff'>{metrics['last_refresh']}</span>", unsafe_allow_html=True)
    with c6:
        st.markdown(f"**USER ROLE**<br><span style='color:#28a745'>{metrics['user_role']}</span>", unsafe_allow_html=True)
    
    st.markdown("---")

def render_sidebar():
    with st.sidebar:
        st.title("COMMAND CONTROL")
        st.markdown("---")
        
        # Mode Toggles
        mode = st.radio("OPERATING MODE", ["🔴 LIVE MONITORING", "🔍 DEEP SCAN", "🔮 PREDICTIVE", "🎲 SIMULATION"])
        
        st.markdown("### FILTER PARAMETERS")
        time_window = st.selectbox("TIME WINDOW", ["Last 1 Hour", "Last 24 Hours", "Last 7 Days", "Quarterly"])
        threat_level = st.multiselect("THREAT LEVEL", ["CRITICAL", "HIGH", "MEDIUM", "LOW"], default=["CRITICAL", "HIGH"])
        
        st.markdown("### SOURCE CALIBRATION")
        st.slider("MIN CONFIDENCE THRESHOLD", 0, 100, 80)
        st.slider("SOURCE RELIABILITY WEIGHT", 0.0, 1.0, 0.8)
        
        st.markdown("### SCOPE")
        st.selectbox("PRIMARY REGION", ["Global", "Indo-Pacific", "Euro-Atlantic", "Middle East"])
        st.text_input("CUSTOM ASSET QUERY", placeholder="e.g. 'Semiconductor Supply Chain'")
        
        st.markdown("---")
        st.info(f"System Status: ONLINE\nLatency: 42ms\nSecure Uplink: ACTIVE")

def render_war_room_map():
    assets = SentinelBackend.get_map_assets()
    
    # Folium Map Setup
    m = folium.Map(location=[20, 80], zoom_start=2, tiles="CartoDB dark_matter", width="100%", height="400px")
    
    risk_colors = {"CRITICAL": "red", "HIGH": "orange", "MEDIUM": "yellow", "LOW": "green"}
    
    for asset in assets:
        color = risk_colors.get(asset["risk"], "grey")
        
        # Asset Marker
        folium.CircleMarker(
            location=[asset["lat"], asset["lon"]],
            radius=8 if asset["risk"] == "CRITICAL" else 5,
            popup=f"<b>{asset['name']}</b><br>Risk: {asset['risk']}<br>Conf: {asset['conf']}%",
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7
        ).add_to(m)
        
        # Simulated Pulse for Critical
        if asset["risk"] == "CRITICAL":
            folium.Circle(
                location=[asset["lat"], asset["lon"]],
                radius=500000,
                color=color,
                weight=1,
                fill=True,
                fill_opacity=0.1
            ).add_to(m)

    st_folium(m, height=400, use_container_width=True)

def render_intelligence_feed():
    st.subheader("INTELLIGENCE STREAM")
    events = SentinelBackend.get_intelligence_feed()
    
    for evt in events:
        badge_class = f"badge-{evt['severity'].lower()}"
        
        with st.expander(f"{evt['headline']}"):
            # Header Line
            st.markdown(f"""
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span class='{badge_class}'>{evt['severity']}</span>
                <span style='color: #888; font-size: 0.8rem;'>{evt['timestamp']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Asset:** {evt['asset']}")
                st.markdown(f"**Category:** {evt['category']}")
            with c2:
                st.markdown(f"**Confidence:** {evt['confidence']}%")
                st.markdown(f"**Source:** {evt['source']}")
                
            st.markdown(f"**Analysis:** {evt['why']}")
            st.button("ACTION: INITIATE RESPONSE", key=evt['id'])

def render_analytics_tabs():
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 ANALYTICS", 
        "🕸️ DIGITAL TWIN", 
        "🎲 SIMULATION", 
        "🔔 ALERTING", 
        "🕵️ ANALYST", 
        "📜 LOGS"
    ])
    
    # 1. Analytics Tab
    with tab1:
        st.markdown("#### RISK VELOCITY & ROOT CAUSE")
        _, _, velocity_df, cause_df = SentinelBackend.get_analytics_data()
        
        c1, c2 = st.columns(2)
        with c1:
            line_chart = alt.Chart(velocity_df).mark_line(color='#00d4ff').encode(
                x='time', y='risk_score'
            ).properties(height=200)
            st.altair_chart(line_chart, use_container_width=True)
        with c2:
            donut = alt.Chart(cause_df).mark_arc(innerRadius=50).encode(
                theta='count', color='cause'
            ).properties(height=200)
            st.altair_chart(donut, use_container_width=True)
            
    # 2. Digital Twin Tab (Graphviz)
    with tab2:
        st.markdown("#### SUPPLY CHAIN DEPENDENCY GRAPH")
        graph = graphviz.Digraph()
        graph.attr(rankdir='LR', bgcolor='transparent')
        graph.attr('node', shape='box', style='filled', color='white', fontname='Roboto')
        
        graph.node('A', 'Taiwan Semi (TSMC)', fillcolor='#ffcccc') # Critical
        graph.node('B', 'Assembly (Foxconn)', fillcolor='#ffffcc')
        graph.node('C', 'Logistics (Evergreen)', fillcolor='#ffffcc')
        graph.node('D', 'OEM (Apple)', fillcolor='#ccffcc')
        graph.node('E', 'Defense (Raytheon)', fillcolor='#ffcccc') # Critical
        
        graph.edge('A', 'B', label='Chip Supply')
        graph.edge('B', 'C', label='Finished Goods')
        graph.edge('C', 'D', label='Consumer')
        graph.edge('A', 'E', label='Mil-Spec')
        
        st.graphviz_chart(graph)
        st.caption("🔴 Critical Node Exposure Detected in Upstream Tier-1")

    # 3. Simulation Tab
    with tab3:
        st.markdown("#### SCENARIO: STRAIT BLOCKADE (7 DAYS)")
        
        col_sim1, col_sim2 = st.columns(2)
        with col_sim1:
            duration = st.slider("Disruption Duration (Days)", 1, 30, 7)
            severity = st.select_slider("Blockade Severity", options=["Partial", "Significant", "Total"])
        
        with col_sim2:
            st.metric("Projected Revenue Risk", f"${duration * 12.5}M", "High Confidence")
            st.metric("Inventory Coverage", f"{max(0, 14 - duration)} Days", "-40%")
            
        st.progress(min(100, duration * 3))
        st.caption("Probability of cascading failure: 84%")

    # 4. Alerting Tab
    with tab4:
        st.markdown("#### ESCALATION RULES")
        st.text_input("Rule Name", value="Tier-1 Supplier Critical Event")
        c1, c2 = st.columns(2)
        with c1:
            st.number_input("Confidence Threshold >", value=90)
        with c2:
            st.multiselect("Channels", ["Email", "Slack", "PagerDuty"], default=["Slack", "PagerDuty"])
        st.toggle("Require Human-in-the-Loop Approval", value=True)
        st.button("Save Rule Configuration")

    # 5. Analyst Workbench
    with tab5:
        st.markdown("#### PENDING REVIEW QUEUE")
        cols = st.columns([3, 1, 1])
        cols[0].markdown("**Event: Unverified Drone Sighting (Red Sea)**")
        cols[1].button("✅ APPROVE", type="primary")
        cols[2].button("❌ DISMISS")
        st.text_area("Analyst Annotation", placeholder="Add context...")

    # 6. Audit Logs
    with tab6:
        st.markdown("#### SYSTEM AUDIT TRAIL")
        logs = SentinelBackend.get_logs()
        st.dataframe(logs, use_container_width=True, hide_index=True)
        st.download_button("Export Compliance Report (PDF)", "report", "application/pdf")

def render_footer():
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.caption("🔒 DATA ACCESS: LEVEL 5 (TOP SECRET)")
    with c2: st.caption("🔑 API KEY: sk_live_...94x")
    with c3: st.caption("📡 MODEL STATUS: OPERATIONAL")
    with c4: st.caption("🏥 SYSTEM HEALTH: 99.99% UPTIME")

# -----------------------------------------------------------------------------
# 4. MAIN APPLICATION ORCHESTRATION
# -----------------------------------------------------------------------------
def main():
    # 1. Header
    render_global_header()
    
    # 2. Sidebar Controls
    render_sidebar()
    
    # 3. War Room Map (Row 1)
    st.markdown("### 🗺️ WAR ROOM: ACTIVE THEATER")
    render_war_room_map()
    
    # 4. Split Layout (Row 2)
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        render_intelligence_feed()
        
    with col_right:
        render_analytics_tabs()
        
    # 5. Footer
    render_footer()

if __name__ == "__main__":
    main()
