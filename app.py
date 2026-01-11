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
# PAGE CONFIG & BASIC STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AVELLON | Global Risk OS",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern dark theme with better structure + CSS variables
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

    .stApp {
        background-color: var(--bg);
        color: var(--text-primary);
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }

    /* Cards */
    .card {
        background: var(--surface);
        border-radius: 10px;
        border: 1px solid var(--border);
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        transition: all 0.2s ease;
    }
    .card:hover {
        background: var(--surface-hover);
        transform: translateY(-2px);
    }

    /* Better metrics */
    .metric-card {
        background: var(--surface);
        border-radius: 10px;
        border-left: 4px solid var(--accent);
        padding: 1.2rem 1.4rem;
        text-align: center;
        min-height: 110px;
    }
    .metric-value {
        font-size: 2.2rem !important;
        font-weight: 700;
        color: var(--text-primary);
    }
    .metric-label {
        font-size: 0.85rem !important;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 0.4rem;
    }

    /* Status badges */
    .badge {
        padding: 5px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-critical { background: var(--critical); color: white; }
    .badge-high     { background: var(--high); color: black; }
    .badge-medium   { background: var(--medium); color: black; }
    .badge-low      { background: var(--low); color: white; }

    /* Chat */
    .chat-container {
        background: var(--surface);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.8rem 0;
    }
    .chat-user {
        background: #0e1a2f;
        border-left: 4px solid var(--accent);
    }
    .chat-ai {
        background: #13251f;
        border-left: 4px solid var(--low);
    }

    hr {
        border-color: var(--border) !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BACKEND (unchanged logic)
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
        velocity = pd.DataFrame({
            'time': pd.date_range(start='2024-01-01', periods=10, freq='H'),
            'risk_score': [20, 22, 25, 24, 30, 45, 50, 65, 72, 72]
        })
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
# MODERN COMPONENTS
# -----------------------------------------------------------------------------
def metric_card(label, value, delta=None, color="var(--accent)"):
    delta_str = f"Δ {delta}" if delta else ""
    # Ensure delta is treated as a string before checking characters
    delta_val = str(delta) if delta else ""
    delta_color = color if delta and "+" in delta_val else "var(--text-secondary)"
    
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: {color}">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        <div style="color:{delta_color}; font-size:0.9rem; margin-top:0.3rem;">{delta_str}</div>
    </div>
    """, unsafe_allow_html=True)

def render_header():
    metrics = SentinelBackend.get_global_metrics()
    cols = st.columns([1,1,1,1,1.6,1.2])

    with cols[0]:
        # Fix: Passed CSS variables as strings
        metric_card("GLOBAL RISK INDEX", f"{metrics['risk_index']}", "+2.4%", "var(--critical)")
    with cols[1]:
        metric_card("ACTIVE CRITICAL", metrics['critical_events'], "Alerts", "var(--critical)")
    with cols[2]:
        metric_card("ESCALATING", metrics['escalating'], "Assets", "var(--high)")
    with cols[3]:
        metric_card("STABLE", f"{metrics['stable_pct']}%", None, "var(--low)")
    with cols[4]:
        st.markdown(f"""
        <div class="card" style="text-align:center; padding:1.1rem;">
            <div style="color:var(--text-secondary); font-size:0.82rem; text-transform:uppercase;">LIVE TIME (GMT)</div>
            <div style="font-size:1.38rem; color:var(--accent); font-weight:600; margin-top:0.3rem;">
                {metrics['last_refresh']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with cols[5]:
        st.markdown(f"""
        <div class="card" style="text-align:center; padding:1.1rem;">
            <div style="color:var(--text-secondary); font-size:0.82rem; text-transform:uppercase;">CURRENT ROLE</div>
            <div style="font-size:1.32rem; color:var(--low); font-weight:600; margin-top:0.3rem;">
                {metrics['user_role']}
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.title("🛡️ AVELLON")
        st.caption(f"Command & Control • {SentinelBackend.get_live_gmt_time()}")
        st.markdown("---")

        st.subheader("Operating Mode")
        mode = st.radio("", 
            ["🔴 LIVE MONITORING", "🔍 DEEP SCAN", "🔮 PREDICTIVE", "🎲 SIMULATION"],
            label_visibility="collapsed")

        st.markdown("### Active Filters")
        threat_levels = st.multiselect("Threat Level", 
            ["CRITICAL", "HIGH", "MEDIUM", "LOW"], 
            default=["CRITICAL", "HIGH"])

        st.markdown("---")
        st.info("System Status: **ONLINE**\nSatellites: **CONNECTED**\nAvg Latency: **42ms**", icon="✅")

def render_map_section():
    st.markdown("### 🗺️ WAR ROOM – Live Theater (NASA GIBS Overlay)")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    assets = SentinelBackend.get_map_assets()
    m = folium.Map(location=[20, 80], zoom_start=2, tiles=None)

    folium.TileLayer('CartoDB dark_matter', name="Tactical Dark").add_to(m)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    folium.TileLayer(
        tiles=f'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{today}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg',
        attr='NASA GIBS • Live Daily',
        name='NASA Satellite (True Color)',
        overlay=True,
        control=True,
        opacity=0.65
    ).add_to(m)

    risk_colors = {"CRITICAL": "#f85149", "HIGH": "#f0883e", "MEDIUM": "#d2a241", "LOW": "#3fb950"}

    for asset in assets:
        color = risk_colors.get(asset["risk"], "#666")
        folium.CircleMarker(
            location=[asset["lat"], asset["lon"]],
            radius=10 if asset["risk"] == "CRITICAL" else 7,
            popup=f"<b>{asset['name']}</b><br>Risk: {asset['risk']} • Confidence: {asset['conf']}%",
            color=color, fill=True, fill_color=color, fill_opacity=0.75
        ).add_to(m)

        if asset["risk"] == "CRITICAL":
            folium.Circle(location=[asset["lat"], asset["lon"]], radius=600000,
                          color=color, weight=1.5, fill=True, fill_opacity=0.12).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, height=480, use_container_width=True)

# -----------------------------------------------------------------------------
# MAIN LAYOUT
# -----------------------------------------------------------------------------
def main():
    render_header()
    render_sidebar()

    # Main content area
    col_map, col_side = st.columns([2.4, 1])

    with col_map:
        render_map_section()

    with col_side:
        # Intelligence Feed
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("📡 INTELLIGENCE STREAM")
            
            pdf_data = SentinelBackend.generate_pdf_brief()
            st.download_button(
                "📄 Download Full Brief (PDF)",
                data=pdf_data,
                file_name=f"Avellon_Brief_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )

            for evt in SentinelBackend.get_intelligence_feed():
                badge_class = f"badge badge-{evt['severity'].lower()}"
                with st.expander(f"{evt['headline']}"):
                    st.markdown(f"<span class='{badge_class}'>{evt['severity']}</span>  {evt['timestamp']}", unsafe_allow_html=True)
                    st.caption(f"{evt['category']} • {evt['source']}")
                    st.write("**Why it matters:**", evt['why'])
                    if st.button("Initiate Response Protocol", key=f"act_{evt['id']}"):
                        st.info("Response protocol initiated (simulation mode)", icon="⚡")
            st.markdown("</div>", unsafe_allow_html=True)

    # Tabs section
    st.markdown("---")
    tab_analytics, tab_chat, tab_twin, tab_sim, tab_logs = st.tabs(
        ["📊 Analytics", "💬 AI Analyst", "🕸️ Digital Twin", "🎲 Simulation", "📜 Logs"]
    )

    with tab_analytics:
        _, _, velocity_df, cause_df = SentinelBackend.get_analytics_data()

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Risk Velocity (last 10 hours)**")
            st.altair_chart(
                alt.Chart(velocity_df)
                .mark_line(color='#58a6ff', point=True)
                .encode(x='time', y='risk_score')
                .properties(height=240),
                use_container_width=True
            )

        with c2:
            st.markdown("**Root Cause Distribution**")
            st.altair_chart(
                alt.Chart(cause_df)
                .mark_arc(innerRadius=60)
                .encode(theta='count', color='cause')
                .properties(height=240),
                use_container_width=True
            )

    with tab_chat:
        st.markdown("#### 💬 Fusion Intelligence Analyst")
        st.caption("Satellite • SIGINT • OSINT • Dark Web • ERP")

        chat_container = st.container(height=420)

        with chat_container:
            for msg in st.session_state['chat_history']:
                cls = "chat-user" if msg['role'] == "user" else "chat-ai"
                with st.chat_message(msg['role'], avatar="🧑‍💻" if msg['role']=='user' else "🛡️"):
                    st.markdown(msg['content'])

        prompt = st.chat_input("Ask about any asset, corridor, or financial impact...")

        if prompt:
            st.session_state['chat_history'].append({"role": "user", "content": prompt})

            with st.spinner("Fusing multi-source intelligence..."):
                time.sleep(1.2)
                response = SentinelBackend.ai_chat_response(prompt)
                st.session_state['chat_history'].append({"role": "AI", "content": response})

            st.rerun()

    with tab_twin:
        st.markdown("#### Supply Chain Digital Twin – Example")
        g = graphviz.Digraph()
        g.attr(rankdir='LR', bgcolor='transparent', fontname='Segoe UI')
        g.attr('node', shape='box', style='filled', fillcolor='#1f2937', fontcolor='white', fontname='Segoe UI')
        g.node('A', 'Taiwan Semi', fillcolor='#4a1c1c')
        g.node('B', 'Assembly', fillcolor='#3a2e1c')
        g.node('C', 'Logistics', fillcolor='#1c3a2e')
        g.node('D', 'Apple', fillcolor='#1c2e4a')
        g.edge('A', 'B')
        g.edge('B', 'C')
        g.edge('C', 'D')
        st.graphviz_chart(g, use_container_width=True)

    with tab_sim:
        st.markdown("#### Scenario Simulation Engine")
        days = st.slider("Simulation Duration (days)", 1, 30, 7)
        risk_value = days * 12.5
        st.metric("Estimated Revenue Risk", f"${risk_value:,.1f}M", delta="High Confidence")
        st.progress(min(100, days * 3.5))

    with tab_logs:
        st.dataframe(
            SentinelBackend.get_logs().style.set_properties(**{'background':'var(--surface)', 'color':'var(--text-primary)'}),
            use_container_width=True,
            hide_index=True
        )

    # Footer
    st.markdown("---")
    cols = st.columns(4)
    cols[0].caption("🔒 DATA ACCESS LEVEL: 5 (TOP SECRET)")
    cols[1].caption("🔑 API KEY: sk_live_...94x")
    cols[2].caption("📡 SATELLITE FEED: NASA GIBS • ACTIVE")
    cols[3].caption("🏥 SYSTEM HEALTH: 99.99% • ONLINE")

if __name__ == "__main__":
    main()
