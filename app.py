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

# --- CONFIGURATION: SUPPLY CHAIN GRAPH ---
# This maps assets to their downstream dependencies.
# If the Key has a risk, the Values (Children) get a "Warning".
SUPPLY_CHAIN_MAP = {
    "Taiwan Strait": ["TSMC (Taiwan)", "Foxconn (China)", "Apple (USA)", "Nvidia (USA)"],
    "Strait of Malacca": ["Port of Singapore", "Tesla Giga Shanghai", "Toyota (Japan)", "Rotterdam Hub"],
    "Red Sea Corridor": ["Maersk Line", "Hapag-Lloyd", "Volkswagen (EU)", "IKEA Global"],
    "Gulf of Mexico Energy": ["Pemex", "ExxonMobil Refineries", "US Plastics Industry"],
}

# --- ASSET DATABASE WITH PREDICTIVE METADATA ---
GEO_ASSETS = {
    "Panama Canal": {"coords": [9.101, -79.695], "query": '"Panama Canal" OR "Gatun Lake"', "region": "Americas", "type": "Choke Point"},
    "Gulf of Mexico Energy": {"coords": [25.000, -90.000], "query": '"Gulf of Mexico oil" OR "Pemex platform"', "region": "Americas", "type": "Energy Asset"},
    "Red Sea Corridor": {"coords": [20.000, 38.000], "query": '"Red Sea" OR "Suez Canal" OR "Houthi"', "region": "MENA", "type": "Trade Route"},
    "Strait of Hormuz": {"coords": [26.566, 56.416], "query": '"Strait of Hormuz" OR "Iranian navy"', "region": "MENA", "type": "Choke Point"},
    "Strait of Malacca": {"coords": [4.000, 100.000], "query": '"Strait of Malacca" OR "Singapore Strait"', "region": "Indo-Pacific", "type": "Choke Point"},
    "Taiwan Strait": {"coords": [24.000, 119.000], "query": '"Taiwan Strait" OR "PLA navy" OR "TSMC"', "region": "Indo-Pacific", "type": "Conflict Zone"},
    "South China Sea": {"coords": [12.000, 113.000], "query": '"South China Sea" OR "Spratly Islands"', "region": "Indo-Pacific", "type": "Conflict Zone"},
    "Rotterdam Port": {"coords": [51.922, 4.477], "query": '"Port of Rotterdam" OR "Maasvlakte"', "region": "Europe", "type": "Port Terminal"}
}

EVENT_PATTERNS = {
    "Military Conflict": [r"missile", r"drone", r"navy", r"warship", r"attack", r"fired"],
    "Supply Chain Delay": [r"blocked", r"grounded", r"suspended", r"congestion", r"delay", r"collision"],
    "Regulatory Sanction": [r"sanction", r"seized", r"ban", r"tariff", r"customs"],
    "Natural Disaster": [r"cyclone", r"typhoon", r"earthquake", r"tsunami", r"flood"]
}

# --- ENGINE 1: INTELLIGENCE & PREDICTION ---
class PredictiveEngine:
    def __init__(self):
        self.headers = {'User-Agent': 'SentinelNode-Predictor'}

    def fetch_feed(self, url):
        try: return feedparser.parse(url)
        except: return None

    def calculate_risk_velocity(self, current_risk_score):
        """
        Simulates historical comparison. 
        In production, this queries a database of yesterday's scores.
        """
        # Mocking 'Yesterday's Score' for demo purposes
        yesterday_score = current_risk_score * random.uniform(0.8, 1.2)
        velocity = ((current_risk_score - yesterday_score) / yesterday_score) * 100
        return velocity

    def predict_delay_prob(self, risk_velocity, category):
        """Predicts probability of shipping delays based on risk trend."""
        base_prob = 10
        if risk_velocity > 0: base_prob += 20
        if risk_velocity > 20: base_prob += 40
        if category == "Supply Chain Delay": base_prob += 20
        return min(base_prob, 95)

    def scan_target(self, query):
        base = query.replace(" ", "%20")
        url = f"https://news.google.com/rss/search?q={base}%20when:7d&hl=en-IN&gl=IN&ceid=IN:en"
        feed = self.fetch_feed(url)
        results = []
        
        total_risk_accum = 0

        if feed and feed.entries:
            for entry in feed.entries[:10]:
                text = f"{entry.title} {entry.get('summary', '')}"
                blob = TextBlob(text)
                
                # Logic
                category = "General Risk"
                for cat, pats in EVENT_PATTERNS.items():
                    if any(re.search(p, text.lower()) for p in pats):
                        category = cat; break
                
                risk_val = 1 # Low
                if blob.sentiment.polarity < -0.05: risk_val = 2 # Med
                if blob.sentiment.polarity < -0.2: risk_val = 3 # High
                if category == "Military Conflict" and risk_val >= 2: risk_val = 4 # Crit

                total_risk_accum += risk_val
                
                risk_label = ["LOW", "MEDIUM", "HIGH", "CRITICAL"][risk_val-1]

                results.append({
                    "Title": entry.title,
                    "Link": entry.link,
                    "Date": entry.published if hasattr(entry, 'published') else "Recent",
                    "Risk": risk_label,
                    "RiskVal": risk_val,
                    "Category": category,
                    "Source": entry.source.get('title', 'Unknown')
                })
        
        # Calculate Prediction Metrics
        avg_risk = total_risk_accum / len(results) if results else 1
        velocity = self.calculate_risk_velocity(avg_risk)
        delay_prob = self.predict_delay_prob(velocity, results[0]['Category'] if results else "None")

        return results, velocity, delay_prob

# --- ENGINE 2: AIS TRAFFIC SIMULATOR ---
def generate_ais_traffic(center_coords, traffic_density="Normal"):
    """
    Simulates real-time AIS vessel data points around a choke point.
    Real API costs $50k/yr. This simulates the visualization value.
    """
    ships = []
    num_ships = 10 if traffic_density == "Normal" else 5
    
    for _ in range(num_ships):
        # Random scatter around the center
        lat = center_coords[0] + random.uniform(-0.5, 0.5)
        lon = center_coords[1] + random.uniform(-0.5, 0.5)
        
        ship_types = ["Container Ship", "Oil Tanker", "Bulk Carrier"]
        status = "Underway using engine"
        
        # If High Risk, simulate deviations
        if traffic_density == "Disrupted":
            status = "Drifting / Awaiting Orders" if random.random() > 0.5 else "Rerouting"
        
        ships.append({
            "name": f"Vessel-{random.randint(1000,9999)}",
            "type": random.choice(ship_types),
            "coords": [lat, lon],
            "status": status
        })
    return ships

# --- FRONTEND UI ---
st.set_page_config(page_title="SENTINEL-NODE V19", layout="wide")

if 'active_scan' not in st.session_state: st.session_state['active_scan'] = None
if 'alerts' not in st.session_state: st.session_state['alerts'] = []

st.title("🔮 Sentinel-Node: Predictive Logistics")
st.markdown("### Stage 2: Foresight & Supply Chain Integration")

# --- SIDEBAR: ALERT CENTER ---
st.sidebar.title("🔔 Alert Center")
if st.sidebar.button("Clear Alerts"): st.session_state['alerts'] = []

if st.session_state['alerts']:
    for alert in st.session_state['alerts']:
        st.sidebar.error(alert)
else:
    st.sidebar.info("No active push notifications.")

st.sidebar.markdown("---")
st.sidebar.caption("System Modules Active:")
st.sidebar.checkbox("Predictive Risk Engine", value=True, disabled=True)
st.sidebar.checkbox("AIS Traffic Simulator", value=True, disabled=True)
st.sidebar.checkbox("Dependency Graphing", value=True, disabled=True)

# --- MAP LAYER ---
# Base Map
m = folium.Map(location=[20.0, 0.0], zoom_start=2, tiles="CartoDB dark_matter")

# Add Static Asset Markers
for name, data in GEO_ASSETS.items():
    color = "red" if data['type'] == "Conflict Zone" else "orange" if data['type'] == "Choke Point" else "blue"
    folium.Marker(data['coords'], popup=name, icon=folium.Icon(color=color, icon="info-sign")).add_to(m)

# Logic: If we have an active scan, show the AIS ships for that region
if st.session_state['active_scan']:
    target = st.session_state['active_scan']['target']
    risk_level = st.session_state['active_scan']['prediction']['delay_prob']
    
    # Determine traffic state based on predicted risk
    traffic_state = "Disrupted" if risk_level > 50 else "Normal"
    
    # Generate Ships
    ships = generate_ais_traffic(GEO_ASSETS[target]['coords'], traffic_state)
    
    # Add Ships to Map
    for ship in ships:
        ship_color = "green" if ship['status'] == "Underway using engine" else "red"
        folium.CircleMarker(
            location=ship['coords'],
            radius=4,
            color=ship_color,
            fill=True,
            popup=f"<b>{ship['name']}</b><br>{ship['type']}<br>Status: {ship['status']}"
        ).add_to(m)

st_data = st_folium(m, height=400, width="100%")

# --- LOGIC: EXECUTE PREDICTION ---
trigger = None
if st_data and st_data.get("last_object_clicked_popup"):
    clicked = st_data["last_object_clicked_popup"]
    if clicked in GEO_ASSETS: trigger = clicked

engine = PredictiveEngine()

if trigger:
    with st.spinner(f"🧠 Calculating Predictive Risk Models for: {trigger}..."):
        res, velocity, delay_prob = engine.scan_target(GEO_ASSETS[trigger]['query'])
        
        # Save to state
        st.session_state['active_scan'] = {
            'target': trigger, 
            'data': res,
            'prediction': {'velocity': velocity, 'delay_prob': delay_prob}
        }
        
        # Trigger Push Alert if Risk is High (Simulation)
        if delay_prob > 60:
            alert_msg = f"⚠️ HIGH PREDICTION: {trigger} delay probability rose to {int(delay_prob)}%. Notification sent to Slack/Teams."
            if alert_msg not in st.session_state['alerts']:
                st.session_state['alerts'].append(alert_msg)

# --- DASHBOARD ---
if st.session_state['active_scan']:
    scan = st.session_state['active_scan']
    data = scan['data']
    pred = scan['prediction']
    target = scan['target']
    
    st.markdown("---")
    st.header(f"📊 Predictive Analysis: {target}")

    # 1. Prediction Cards
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.metric("Risk Velocity (24h Trend)", f"{pred['velocity']:.1f}%", delta_color="inverse")
        st.caption("Speed of risk escalation vs yesterday")
        
    with c2:
        prob_color = "red" if pred['delay_prob'] > 50 else "green"
        st.metric("Predicted Delay Probability", f"{int(pred['delay_prob'])}%")
        st.progress(int(pred['delay_prob'])/100)
        
    with c3:
        status = "CRITICAL" if pred['delay_prob'] > 70 else "WARNING" if pred['delay_prob'] > 40 else "STABLE"
        st.metric("Operational Status", status)

    st.markdown("---")

    # 2. Supply Chain Impact Graph (The "Ripple Effect")
    c_graph, c_feed = st.columns([1, 1])
    
    with c_graph:
        st.subheader("🔗 Supply Chain Impact Graph")
        st.caption(f"If {target} fails, these entities are At Risk:")
        
        # Build Graph
        graph = graphviz.Digraph()
        graph.attr(rankdir='LR')
        
        # Root Node
        root_color = "red" if pred['delay_prob'] > 60 else "orange"
        graph.node(target, style="filled", fillcolor=root_color, color="black")
        
        # Dependencies
        dependencies = SUPPLY_CHAIN_MAP.get(target, ["Global Shipping", "Regional Logistics"])
        
        for dep in dependencies:
            # Logic: If root is bad, children are "At Risk" (Yellow)
            child_color = "yellow" if pred['delay_prob'] > 40 else "lightgrey"
            graph.node(dep, style="filled", fillcolor=child_color)
            graph.edge(target, dep, label="Impact Flow")
            
        st.graphviz_chart(graph)

    # 3. Intelligence Feed
    with c_feed:
        st.subheader("📋 Causal Factors (News)")
        df = pd.DataFrame(data)
        if not df.empty:
            for _, row in df[:5].iterrows():
                 icon = "🔴" if row['Risk'] == "CRITICAL" else "🟠" if row['Risk'] == "HIGH" else "🟢"
                 st.write(f"{icon} **{row['Category']}**: {row['Title']}")
                 st.caption(f"Source: {row['Source']}")
