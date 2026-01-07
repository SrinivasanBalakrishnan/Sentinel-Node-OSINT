import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import graphviz
import folium
from streamlit_folium import st_folium
from datetime import datetime, timezone
import random
import time
from PIL import Image, ImageDraw
import uuid
from fpdf import FPDF
import base64

# -----------------------------------------------------------------------------
# 1. CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AVELLON INTELLIGENCE",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Command Center" Aesthetic
st.markdown("""
<style>
    .stApp { background-color: #0b0d10; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #f0f2f6; letter-spacing: -0.5px; }
    .css-card { background-color: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 6px; margin-bottom: 10px; }
    div[data-testid="stMetricValue"] { font-family: 'Roboto Mono', monospace; color: #e0e0e0; }
    .badge-critical { background: #7f1d1d; color: #fecaca; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; border: 1px solid #991b1b; }
    .badge-high { background: #7c2d12; color: #fed7aa; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; border: 1px solid #c2410c; }
    .chat-message { padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    .chat-user { background-color: #2b3137; border-left: 3px solid #00d4ff; }
    .chat-ai { background-color: #1c2128; border-left: 3px solid #28a745; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. BACKEND LOGIC & DATA FUSION
# -----------------------------------------------------------------------------
if 'page' not in st.session_state: st.session_state['page'] = 'Home'
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'chat_history' not in st.session_state: st.session_state['chat_history'] = []

# --- ASSET DATABASE ---
GEO_ASSETS = {
    "Panama Canal": {"coords": [9.101, -79.695], "type": "Choke Point", "risk": "LOW"},
    "Red Sea Corridor": {"coords": [20.000, 38.000], "type": "Trade Route", "risk": "CRITICAL"},
    "Taiwan Strait": {"coords": [24.000, 119.000], "type": "Conflict Zone", "risk": "HIGH"},
    "Strait of Malacca": {"coords": [4.000, 100.000], "type": "Choke Point", "risk": "MEDIUM"},
    "Rotterdam Hub": {"coords": [51.922, 4.477], "type": "Port", "risk": "LOW"},
    "Gulf of Mexico": {"coords": [25.000, -90.000], "type": "Energy", "risk": "MEDIUM"}
}

class AvellonBackend:
    @staticmethod
    def get_gmt_time():
        """Returns live GMT/UTC time, auto-corrected."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S GMT")

    @staticmethod
    def get_intel_feed():
        return [
            {"title": "Unverified Drone Activity", "loc": "Red Sea Sector 4", "severity": "CRITICAL", "cat": "Conflict", "time": "14m ago", "conf": 94},
            {"title": "Typhoon Beryl Formation", "loc": "Philippine Sea", "severity": "HIGH", "cat": "Weather", "time": "42m ago", "conf": 88},
            {"title": "Port Labor Strike Notice", "loc": "Hamburg Terminal", "severity": "MEDIUM", "cat": "Labor", "time": "2h ago", "conf": 76},
        ]

    @staticmethod
    def generate_pdf_report():
        """Generates a downloadable Intelligence Brief PDF."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Header
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="AVELLON INTELLIGENCE BRIEF", ln=1, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=f"Generated: {AvellonBackend.get_gmt_time()} | Classification: SECRET//NOFORN", ln=1, align='C')
        pdf.ln(10)
        
        # Executive Summary
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="1. EXECUTIVE SUMMARY", ln=1, align='L')
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 10, txt="Global risk velocity has increased by 14% in the last 24 hours. Critical friction detected in the Red Sea corridor affecting EU-Asia logistics. Financial blast radius estimation for Tier-1 automotive sector is $45M/day.")
        pdf.ln(5)
        
        # Risk Table
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="2. ACTIVE THREAT VECTORS", ln=1, align='L')
        pdf.set_font("Arial", size=10)
        for asset, data in GEO_ASSETS.items():
            pdf.cell(0, 8, txt=f"- {asset}: {data['risk']} ({data['type']})", ln=1)
            
        return pdf.output(dest='S').encode('latin-1')

    @staticmethod
    def ai_chat_response(query):
        """Simulates a Risk-Aware AI Analyst."""
        query = query.lower()
        time_stamp = AvellonBackend.get_gmt_time()
        
        if "red sea" in query:
            return f"[{time_stamp}] **ANALYSIS:** Red Sea transit volume is down 42% due to Houthi kinetic activity. Insurance premiums up 1500%. **BLAST RADIUS:** High impact on LNG exports to Europe."
        elif "taiwan" in query:
            return f"[{time_stamp}] **ANALYSIS:** PLA Navy activity in Taiwan Strait is nominal but elevated. Semiconductor supply chain risk is STABLE but watchlist status is HIGH."
        elif "malacca" in query:
            return f"[{time_stamp}] **ANALYSIS:** Strait of Malacca reports minor congestion. No kinetic threats detected. Efficiency at 92%."
        elif "financial" in query or "blast radius" in query:
            return f"[{time_stamp}] **CALCULATION:** Current geopolitical friction suggests a global aggregated financial blast radius of $2.4B/day in delayed inventory carrying costs."
        else:
            return f"[{time_stamp}] **SYSTEM:** Query received. Cross-referencing Satellite, Dark Web, and ERP sources. No immediate critical anomalies found for this specific vector."

# -----------------------------------------------------------------------------
# 3. NAVIGATION & LAYOUT
# -----------------------------------------------------------------------------
def sidebar_nav():
    st.sidebar.title("AVELLON")
    st.sidebar.caption(f"TIME: {AvellonBackend.get_gmt_time()}")
    st.sidebar.markdown("---")

    if st.session_state['authenticated']:
        st.sidebar.success(f"COMMANDER ACTIVE")
        menu = ["Global War Room", "🛰️ Satellite Recon", "💬 AI Risk Analyst", "🏴‍☠️ Dark Web Intel", "🕸️ Digital Twin", "🔌 Developer API"]
        selected = st.sidebar.radio("Modules", menu)
        
        st.sidebar.markdown("---")
        if st.sidebar.button("Log Out"):
            st.session_state['authenticated'] = False
            st.session_state['page'] = 'Home'
            st.rerun()
        return selected
    else:
        menu = ["Home", "Platform", "Solutions", "About", "Contact"]
        selected = st.sidebar.radio("Navigation", menu)
        st.sidebar.markdown("---")
        if st.sidebar.button("Secure Login"):
            st.session_state['page'] = "Login"
            st.rerun()
        return selected

# -----------------------------------------------------------------------------
# 4. MODULE RENDERERS
# -----------------------------------------------------------------------------

# --- PUBLIC PAGES ---
def render_home():
    st.title("The Geometry of Risk.")
    st.markdown(f"""
    <div style='background-color: #161b22; padding: 30px; border-left: 5px solid #00d4ff; margin-bottom: 20px;'>
        <h3 style='margin-top:0;'>Operational Pre-cognition.</h3>
        <p style='color: #ccc;'>Current System Time: {AvellonBackend.get_gmt_time()}</p>
        <p>Fusing Outside Data (Satellite, Dark Web) with Inside Data (ERP) to predict financial blast radius.</p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.info("**PREDICTIVE**\n\nForecast financial impact days in advance.")
    c2.info("**OMNISCIENT**\n\nSatellite & Dark Web fusion.")
    c3.info("**AUTONOMOUS**\n\nSelf-healing supply chains.")

def render_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("### SECURE CONSOLE")
        u = st.text_input("Identity")
        p = st.text_input("Keycode", type="password")
        if st.button("Authenticate"):
            if u and p: 
                st.session_state['authenticated'] = True
                st.rerun()

# --- SECURE MODULES ---
def render_war_room():
    st.title("Global War Room (Live)")
    st.caption("Integrated Satellite Layers: NASA GIBS / NOAA")
    
    # 1. Map with Satellite Layers
    c1, c2 = st.columns([3, 1])
    with c1:
        # Create Map centered on Global View
        m = folium.Map(location=[20, 0], zoom_start=2, tiles=None) # Start with no default tiles to allow custom ones
        
        # Base Layer (Dark Matter for Tech Look)
        folium.TileLayer('CartoDB dark_matter', name="Dark Mode (Tactical)").add_to(m)
        
        # LAYER 1: NASA GIBS (Terra MODIS) - True Color
        # Note: We use a specific date or 'best' available. For robust code we use a fixed template url.
        folium.TileLayer(
            tiles='https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2024-05-20/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg',
            attr='NASA GIBS',
            name='NASA Satellite (Optical)',
            overlay=True,
            control=True,
            opacity=0.6
        ).add_to(m)
        
        # LAYER 2: Weather / Clouds (OpenWeatherMap standard layer often used, or NOAA proxy)
        # Using a reliable free cloud layer
        folium.TileLayer(
            tiles='https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=YOUR_API_KEY_HERE', # Placeholder logic, usually requires key. 
            # Switching to a generic functional overlay for demo without key:
            # Stamen Toner is deprecated, sticking to reliable overlays.
            attr='Weather Data',
            name='Cloud Cover (Live)',
            overlay=True,
            control=True,
            opacity=0.4
        ).add_to(m)

        # Asset Markers
        for n, d in GEO_ASSETS.items():
            color = "red" if d['risk'] == "CRITICAL" else "orange" if d['risk'] == "HIGH" else "blue"
            # Pulsing effect for critical
            if d['risk'] == "CRITICAL":
                folium.Circle(
                    location=d['coords'], radius=500000, color=color, fill=True, fill_opacity=0.2
                ).add_to(m)
            folium.Marker(d['coords'], popup=f"{n} ({d['risk']})", icon=folium.Icon(color=color, icon="info-sign")).add_to(m)
            
        folium.LayerControl().add_to(m)
        st_folium(m, height=500, use_container_width=True)

    # 2. Intel Feed & PDF Export
    with c2:
        st.subheader("Intelligence Stream")
        
        # Download Button
        pdf_bytes = AvellonBackend.generate_pdf_report()
        st.download_button(
            label="📄 Download Intel Brief (PDF)",
            data=pdf_bytes,
            file_name=f"Avellon_Brief_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
        
        st.markdown("---")
        for item in AvellonBackend.get_intel_feed():
            st.markdown(f"""
            <div class='css-card'>
                <span class='badge-{item['severity'].lower()}'>{item['severity']}</span>
                <b>{item['title']}</b><br>
                <span style='font-size:0.8rem; color:#aaa'>{item['loc']}</span>
            </div>
            """, unsafe_allow_html=True)

def render_chat():
    st.title("AI Risk Analyst")
    st.caption("Ask about any location, threat vector, or financial blast radius.")
    
    # Display History
    for msg in st.session_state['chat_history']:
        role_class = "chat-user" if msg['role'] == "user" else "chat-ai"
        st.markdown(f"<div class='chat-message {role_class}'><b>{msg['role'].upper()}:</b> {msg['content']}</div>", unsafe_allow_html=True)
    
    # Input
    user_input = st.chat_input("Query Avellon Intelligence...")
    if user_input:
        # User Msg
        st.session_state['chat_history'].append({"role": "user", "content": user_input})
        
        # AI Logic
        with st.spinner("Analyzing Satellite & Dark Web data..."):
            time.sleep(1) # Thinking time
            response = AvellonBackend.ai_chat_response(user_input)
            st.session_state['chat_history'].append({"role": "Avellon", "content": response})
        
        st.rerun()

def render_digital_twin():
    st.title("Digital Twin: Financial Blast Radius")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Outside Data (Geopolitics)")
        st.error("⚠️ Red Sea: Kinetic Activity (Critical)")
        st.warning("⚠️ Panama: Drought (High)")
    with c2:
        st.markdown("#### Inside Data (ERP/Inventory)")
        st.metric("Inventory Impact", "-14 Days Coverage", delta_color="inverse")
        st.metric("Financial Blast Radius", "$2.4M / Day", "Escalating")
    
    # Graph
    graph = graphviz.Digraph()
    graph.attr(bgcolor='transparent', rankdir='LR')
    graph.node('A', 'Geopolitical Event (Red Sea)', fillcolor='#7f1d1d', style='filled', fontcolor='white')
    graph.node('B', 'Logistics Delay (+14 Days)', fillcolor='#c2410c', style='filled', fontcolor='white')
    graph.node('C', 'ERP: Stockout Alert', fillcolor='#c2410c', style='filled', fontcolor='white')
    graph.node('D', 'Financial Loss', fillcolor='#7f1d1d', style='filled', fontcolor='white')
    
    graph.edge('A', 'B')
    graph.edge('B', 'C')
    graph.edge('C', 'D')
    st.graphviz_chart(graph)

def render_satellite_recon():
    st.title("Satellite Reconnaissance (Computer Vision)")
    st.info("Live feed analysis from Sentinel-2 / Landsat Sources")
    target = st.selectbox("Target Sector", ["Red Sea", "Taiwan Strait", "Ukraine Border"])
    if st.button("Analyze Imagery"):
        with st.spinner("Processing Optical Feed..."):
            time.sleep(2)
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Strait_of_Malacca.jpg/1200px-Strait_of_Malacca.jpg", caption="Simulated Feed: Object Detection Active")
            st.success("Analysis Complete: 14 Commercial Vessels, 2 Naval Assets detected.")

def render_dark_web():
    st.title("Dark Web Monitor")
    st.caption("Scanning TOR / I2P Networks")
    st.dataframe(pd.DataFrame([
        {"Source": "LockBit", "Threat": "Ransomware chatter targeting Logistics", "Risk": "HIGH"},
        {"Source": "BreachForums", "Threat": "Database sale: Port Credentials", "Risk": "CRITICAL"}
    ]), use_container_width=True)

def render_api():
    st.title("Developer API")
    st.code(f"sk_live_{uuid.uuid4().hex[:24]}", language="bash")

# -----------------------------------------------------------------------------
# 5. MAIN ROUTER
# -----------------------------------------------------------------------------
selection = sidebar_nav()

if not st.session_state['authenticated']:
    if selection == "Home": render_home()
    elif selection == "Login": render_login()
    else: st.info("Please login to access " + selection)
else:
    if selection == "Global War Room": render_war_room()
    elif selection == "💬 AI Risk Analyst": render_chat()
    elif selection == "🛰️ Satellite Recon": render_satellite_recon()
    elif selection == "🏴‍☠️ Dark Web Intel": render_dark_web()
    elif selection == "🕸️ Digital Twin": render_digital_twin()
    elif selection == "🔌 Developer API": render_api()

st.markdown("<div class='footer'>AVELLON INTELLIGENCE © 2026 | ISO 27001 Certified</div>", unsafe_allow_html=True)
