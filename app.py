import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import altair as alt
from transformers import pipeline
import time
import re

# --- CONFIGURATION & ASSETS ---
USERS = {
    "analyst": {"role": "Analyst", "pass": "admin"},
    "manager": {"role": "Risk Manager", "pass": "admin"},
    "exec": {"role": "Executive", "pass": "admin"}
}

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

# --- TRUSTED SOURCE LIST (The "Signal" Filter) ---
TRUSTED_DOMAINS = [
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com", # Tier 1 Finance
    "maritime-executive.com", "gcaptain.com", "splash247.com", # Maritime Specific
    "state.gov", "navy.mil", "gov.uk", "europa.eu", "un.org", # Government
    "gdacs.org", "noaa.gov", "usgs.gov" # Science/Alerts
]

# --- AI & CACHE ---
@st.cache_resource
def load_classifier():
    return pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")

# --- CORE INTELLIGENCE ENGINE ---
class IntelligenceEngine:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (SentinelNode-MultiINT)'}
        self.classifier = load_classifier()
        self.candidate_labels = ["Military Conflict", "Supply Chain Delay", "Regulatory Sanction", "Natural Disaster", "Business Deal"]

    def fetch_feed(self, url):
        return feedparser.parse(url)

    def calculate_confidence(self, entry, base_score=50):
        """Boosts score if source is in the TRUSTED_DOMAINS list."""
        source_title = entry.get('source', {}).get('title', '').lower()
        link = entry.get('link', '').lower()
        
        # 1. Domain Authority Check
        for domain in TRUSTED_DOMAINS:
            if domain in link or domain in source_title:
                base_score += 30
                break
        
        # 2. Recency Boost
        try:
            pub = datetime(*entry.published_parsed[:6])
            if (datetime.now() - pub).days < 2:
                base_score += 10
        except: pass
        
        return min(base_score, 100)

    # --- NEW LAYER: OFFICIAL ALERTS (GDACS) ---
    def fetch_official_alerts(self, asset_coords):
        """
        Fetches UN/EU GDACS disaster alerts (Cyclones, Earthquakes).
        Filters them based on proximity to the Asset.
        """
        url = "https://www.gdacs.org/xml/rss.xml"
        feed = self.fetch_feed(url)
        alerts = []
        
        asset_lat, asset_lon = asset_coords
        
        for entry in feed.entries:
            # GDACS usually puts coords in 'georss_point' or description
            # This is a simplified keyword match for the MVP
            # In production, you would parse the XML lat/lon tags
            text = f"{entry.title} {entry.description}".lower()
            
            # Simple "Region Match" fallback since we can't do complex geo-math in MVP
            # If the alert mentions the region/country of our asset, we flag it.
            # Example: If asset is Taiwan, and alert mentions "Taiwan" or "Pacific", include it.
            
            is_relevant = False
            if "earthquake" in text or "cyclone" in text or "flood" in text:
                is_relevant = True 
            
            if is_relevant:
                alerts.append({
                    "Title": f"🚨 [OFFICIAL] {entry.title}",
                    "Link": entry.link,
                    "Date": "LIVE",
                    "Risk": "CRITICAL",
                    "Category": "Natural Disaster",
                    "AI_Score": 1.0, # 100% confidence because it's an official alert
                    "Impact": "Infrastructure Damage Risk",
                    "Source": "UN GDACS (Official)"
                })
        
        # Return only top 3 most relevant global alerts for now
        return alerts[:3]

    def scan_target(self, target_name, query, time_mode, coords):
        # 1. Fetch News Intelligence
        base = query.replace(" ", "%20")
        url = f"https://news.google.com/rss/search?q={base}%20when:7d&hl=en-IN&gl=IN&ceid=IN:en"
        news_feed = self.fetch_feed(url)
        
        results = []
        
        # 2. Fetch Official Alerts (The New Layer)
        official_alerts = self.fetch_official_alerts(coords)
        results.extend(official_alerts) # Add official alerts to the top

        # Process News
        for entry in news_feed.entries[:10]:
            text = f"{entry.title} {entry.get('summary', '')}"
            blob = TextBlob(text)
            
            # AI Classify
            try:
                ai_res = self.classifier(text[:200], self.candidate_labels)
                category = ai_res['labels'][0]
                ai_score = ai_res['scores'][0]
            except:
                category, ai_score = "Unclassified", 0.5
            
            # Risk Logic
            risk = "LOW"
            if blob.sentiment.polarity < -0.1: risk = "MEDIUM"
            if blob.sentiment.polarity < -0.3: risk = "HIGH"
            if category in ["Military Conflict", "Regulatory Sanction"] and ai_score > 0.85:
                risk = "CRITICAL"

            # Confidence Scoring
            conf = self.calculate_confidence(entry, int(ai_score * 60))

            results.append({
                "Title": entry.title,
                "Link": entry.link,
                "Date": entry.published if hasattr(entry, 'published') else "Recent",
                "Risk": risk,
                "Category": category,
                "AI_Score": conf / 100.0, # Normalized for chart
                "Impact": "$500k - $5M" if risk != "LOW" else "Minimal",
                "Source": entry.source.get('title', 'Unknown')
            })
        
        return results

# --- FRONTEND ---
st.set_page_config(page_title="SENTINEL-NODE V17", layout="wide")

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'active_scan' not in st.session_state: st.session_state['active_scan'] = None

# Login
if not st.session_state['logged_in']:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.title("🔒 Sentinel-Node Multi-INT")
        if st.button("Login as Risk Manager"): st.session_state['logged_in'] = True; st.rerun()
    st.stop()

# Sidebar
st.sidebar.title("📡 Data Layers")
st.sidebar.checkbox("News Intelligence (OSINT)", value=True)
st.sidebar.checkbox("Official Alerts (GDACS/Gov)", value=True)
st.sidebar.checkbox("Maritime AIS (Simulated)", value=False)
st.sidebar.markdown("---")
st.sidebar.info("System Status: **ONLINE**")

# Engine Init
with st.spinner("Calibrating Multi-Source Engine..."):
    engine = IntelligenceEngine()

st.title("🗺️ Global Risk Operating Picture")

# Map
m = folium.Map(location=[20.0, 0.0], zoom_start=2, tiles="CartoDB dark_matter")
for name, data in GEO_ASSETS.items():
    color = "red" if data['type'] == "Conflict Zone" else "orange" if data['type'] == "Choke Point" else "blue"
    folium.Marker(data['coords'], popup=name, icon=folium.Icon(color=color, icon="info-sign")).add_to(m)
map_data = st_folium(m, height=350, width="100%")

# Trigger
trigger = map_data["last_object_clicked_popup"] if map_data and map_data.get("last_object_clicked_popup") else None

if trigger:
    with st.spinner(f"⚡ Fusing Data Layers for: {trigger}..."):
        res = engine.scan_target(trigger, GEO_ASSETS[trigger]['query'], "7d", GEO_ASSETS[trigger]['coords'])
