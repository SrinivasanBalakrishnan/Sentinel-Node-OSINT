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
import uuid
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# --- CONFIGURATION: MOCK DATASETS ---
DARK_WEB_SOURCES = [
    "BreachForums (TOR)", "LockBit Leaks (.onion)", "XSS.is", "Exploit.in", "Dread Forum"
]

THREAT_ACTORS = [
    "Lazarus Group", "APT29", "Volt Typhoon", "Killnet", "Anonymous Sudan"
]

GEO_ASSETS = {
    "Panama Canal": {"coords": [9.101, -79.695], "query": '"Panama Canal"', "region": "Americas", "type": "Choke Point"},
    "Gulf of Mexico Energy": {"coords": [25.000, -90.000], "query": '"Gulf of Mexico oil"', "region": "Americas", "type": "Energy Asset"},
    "Red Sea Corridor": {"coords": [20.000, 38.000], "query": '"Red Sea"', "region": "MENA", "type": "Trade Route"},
    "Taiwan Strait": {"coords": [24.000, 119.000], "query": '"Taiwan Strait"', "region": "Indo-Pacific", "type": "Conflict Zone"},
    "Strait of Malacca": {"coords": [4.000, 100.000], "query": '"Strait of Malacca"', "region": "Indo-Pacific", "type": "Choke Point"},
}

# --- MODULE 1: SATELLITE COMPUTER VISION ---
def generate_satellite_analysis(target_name):
    """
    Simulates fetching a satellite image and running YOLO/Computer Vision on it.
    Draws bounding boxes on a placeholder image to demonstrate the capability.
    """
    # 1. Create a dummy image (In real life, this comes from Maxar/Planet API)
    img = Image.new('RGB', (800, 450), color=(10, 20, 30))
    d = ImageDraw.Draw(img)
    
    # 2. Simulate "Terrain"
    d.rectangle([50, 200, 750, 400], fill=(20, 40, 60)) # Water/Land
    
    # 3. Simulate Object Detection (Ships/Troops)
    detections = []
    num_objects = random.randint(3, 15)
    
    for i in range(num_objects):
        x = random.randint(100, 700)
        y = random.randint(220, 380)
        w, h = random.randint(20, 50), random.randint(10, 30)
        
        # Color code based on type
        obj_type = random.choice(["Civilian Vessel", "Warship", "Troop Transport"])
        color = "red" if obj_type == "Warship" else "green"
        
        # Draw Bounding Box
        d.rectangle([x, y, x+w, y+h], outline=color, width=2)
        d.text((x, y-10), obj_type, fill=color)
        
        detections.append({"Type": obj_type, "Coords": (x, y), "Confidence": random.uniform(0.85, 0.99)})
    
    # Add Overlay Text
    d.text((10, 10), f"SATELLITE FEED: {target_name.upper()}", fill="white")
    d.text((10, 25), f"SOURCE: SENTINEL-ORBIT-1 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC", fill="white")
    
    return img, detections

# --- MODULE 2: DARK WEB MONITOR ---
def scan_dark_web(target_keywords):
    """
    Simulates scanning TOR hidden services for keyword mentions.
    """
    results = []
    for _ in range(random.randint(2, 6)):
        source = random.choice(DARK_WEB_SOURCES)
        actor = random.choice(THREAT_ACTORS)
        
        # Simulate a chatter snippet
        snippets = [
            f"Selling access to {target_keywords} logistics portal. Price: 5 BTC.",
            f"DDoS attack scheduled for {target_keywords} infrastructure on Friday.",
            f"Leaked employee credentials for {target_keywords} region ops.",
            f"Looking for blueprints of {target_keywords} control systems."
        ]
        
        results.append({
            "Source": source,
            "Actor": actor,
            "Snippet": random.choice(snippets),
            "Severity": "CRITICAL" if "Selling" in snippets else "HIGH",
            "Date": (datetime.now() - timedelta(hours=random.randint(1, 48))).strftime('%Y-%m-%d %H:%M')
        })
    return pd.DataFrame(results)

# --- MODULE 3: API MANAGER ---
def generate_api_key():
    return f"sk_live_{uuid.uuid4().hex[:24]}"

# --- FRONTEND UI ---
st.set_page_config(page_title="SENTINEL-NODE V21", layout="wide")

if 'api_keys' not in st.session_state: st.session_state['api_keys'] = []
if 'usage_stats' not in st.session_state: st.session_state['usage_stats'] = {"requests": 1240, "latency": "45ms", "errors": "0.01%"}

# --- SIDEBAR NAV ---
st.sidebar.title("🌌 Ecosystem")
mode = st.sidebar.radio("Module Selection", 
    ["Global Command (Map)", "🛰️ Satellite Recon", "🏴‍☠️ Dark Web Intel", "🔌 Developer API"])

st.title(f"Sentinel-Node: {mode}")

# ==========================================
# MODE 1: GLOBAL COMMAND (Base Map)
# ==========================================
if mode == "Global Command (Map)":
    st.markdown("### Standard Operating Picture")
    m = folium.Map(location=[20.0, 0.0], zoom_start=2, tiles="CartoDB dark_matter")
    for name, data in GEO_ASSETS.items():
        folium.Marker(data['coords'], popup=name, icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)
    st_folium(m, height=500, width="100%")

# ==========================================
# MODE 2: SATELLITE RECON (Computer Vision)
# ==========================================
elif mode == "🛰️ Satellite Recon":
    st.markdown("### AI-Powered Imagery Analysis")
    st.caption("Automated object detection (Warships, Congestion) on live satellite feeds.")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        target_sat = st.selectbox("Select Target Sector", list(GEO_ASSETS.keys()))
        st.info("Satellite connection established.")
        if st.button("📸 CAPTURE & ANALYZE"):
            with st.spinner("Tasking satellite... Transferring raw optical data... Running CV Models..."):
                time.sleep(2) # Fake latency
                img, data = generate_satellite_analysis(target_sat)
                st.session_state['sat_result'] = {'img': img, 'data': data}

    with col2:
        if 'sat_result' in st.session_state:
            # Display the "Processed" Image
            st.image(st.session_state['sat_result']['img'], caption="Processed Output | YOLOv8 Model Detection", use_container_width=True)
            
            # Display Detection Metrics
            dets = st.session_state['sat_result']['data']
            warships = len([d for d in dets if d['Type'] == 'Warship'])
            civilians = len([d for d in dets if d['Type'] == 'Civilian Vessel'])
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Objects Detected", len(dets))
            m2.metric("Warships Identified", warships, delta_color="inverse")
            m3.metric("Congestion Level", "HIGH" if len(dets) > 10 else "NORMAL")
            
            with st.expander("View Raw Detection Data"):
                st.json(dets)

# ==========================================
# MODE 3: DARK WEB INTEL
# ==========================================
elif mode == "🏴‍☠️ Dark Web Intel":
    st.markdown("### Non-Indexed Threat Monitoring")
    st.caption("Scanning TOR hidden services, I2P, and invite-only hacker forums.")
    
    search_term = st.text_input("Enter Asset Keyword (e.g., 'Panama', 'Shell', 'Pipeline')", value="Maersk")
    
    if st.button("SEARCH UNDERGROUND"):
        with st.spinner("Routing through TOR proxy... Scraping .onion sites..."):
            time.sleep(1.5)
            df_dark = scan_dark_web(search_term)
            st.session_state['dark_data'] = df_dark
            
    if 'dark_data' in st.session_state:
        df = st.session_state['dark_data']
        
        # Threat Cards
        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{row['Source']}** | Actor: *{row['Actor']}*")
                    st.code(row['Snippet'], language="text")
                with c2:
                    st.error(row['Severity'])
                    st.caption(row['Date'])
                    
        st.warning("⚠️ ACTION REQUIRED: Correlate these threats with physical security logs immediately.")

# ==========================================
# MODE 4: DEVELOPER API MARKETPLACE
# ==========================================
elif mode == "🔌 Developer API":
    st.markdown("### API Integration Portal")
    st.caption("Build your own applications on top of the Sentinel-Node Intelligence Stream.")
    
    # API Stats
    st.subheader("Your Usage")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Requests (24h)", st.session_state['usage_stats']['requests'])
    s2.metric("Avg Latency", st.session_state['usage_stats']['latency'])
    s3.metric("Error Rate", st.session_state['usage_stats']['errors'])
    s4.metric("Plan", "Enterprise Gold")
    
    st.markdown("---")
    
    # Key Management
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Authentication")
        if st.button("Generate New Secret Key"):
            new_key = generate_api_key()
            st.session_state['api_keys'].append({"key": new_key, "created": datetime.now().strftime('%Y-%m-%d')})
            st.success("New key generated!")
        
        if st.session_state['api_keys']:
            for k in st.session_state['api_keys']:
                st.code(k['key'], language="bash")
                st.caption(f"Created: {k['created']}")
    
    with c2:
        st.subheader("Documentation (Quick Start)")
        st.markdown("""
        **Endpoint:** `GET /v1/intel/risk-score`
        
        **Request:**
        ```bash
        curl -X GET "[https://api.sentinel-node.com/v1/risk?target=taiwan_strait](https://api.sentinel-node.com/v1/risk?target=taiwan_strait)" \
          -H "Authorization: Bearer sk_live_..."
        ```
        
        **Response:**
        ```json
        {
          "target": "Taiwan Strait",
          "risk_level": "HIGH",
          "confidence": 0.92,
          "active_alerts": 3,
          "forecast": "ESCALATING"
        }
        ```
        """)
