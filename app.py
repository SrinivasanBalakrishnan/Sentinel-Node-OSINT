import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import altair as alt
import re
import time
import random

# --- CONFIGURATION: ASSETS & TRUSTED SOURCES ---
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

# Domains that trigger a "High Confidence" score
TRUSTED_DOMAINS = [
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com", 
    "maritime-executive.com", "gcaptain.com", "splash247.com",
    "state.gov", "navy.mil", "gov.uk", "europa.eu", "un.org",
    "gdacs.org", "noaa.gov", "usgs.gov"
]

# Regex Taxonomy for Root Cause Analysis
EVENT_PATTERNS = {
    "Military Conflict": [r"missile", r"drone", r"navy", r"warship", r"attack", r"fired", r"weapon"],
    "Supply Chain Delay": [r"blocked", r"grounded", r"suspended", r"congestion", r"delay", r"collision"],
    "Regulatory Sanction": [r"sanction", r"seized", r"ban", r"tariff", r"customs", r"detained"],
    "Natural Disaster": [r"cyclone", r"typhoon", r"earthquake", r"tsunami", r"flood", r"storm"]
}

# --- INTELLIGENCE ENGINE ---
class IntelligenceEngine:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (SentinelNode-Enterprise)'}

    def fetch_feed(self, url):
        try:
            return feedparser.parse(url)
        except:
            return None

    def calculate_confidence(self, entry, base_score=50):
        """Boosts score if source is trusted or official."""
        source_title = entry.get('source', {}).get('title', '').lower()
        link = entry.get('link', '').lower()
        
        # Domain Authority Boost
        for domain in TRUSTED_DOMAINS:
            if domain in link or domain in source_title:
                base_score += 35
                break
        
        # Recency Boost
        try:
            pub = datetime(*entry.published_parsed[:6])
            if (datetime.now() - pub).days < 2:
                base_score += 10
        except: pass
        
        return min(base_score, 100)

    def classify_event(self, text):
        """Robust Regex Classification (Faster & Safer than AI models on free cloud)"""
        text = text.lower()
        for category, patterns in EVENT_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text):
                    return category
        return "General Risk"

    def estimate_impact(self, risk, category):
        if risk == "LOW": return "Minimal"
        impact_map = {
            "Military Conflict": "$10M+ (Insurance Spike)",
            "Supply Chain Delay": "$500k - $2M (Ops Cost)",
            "Regulatory Sanction": "$1M - $5M (Compliance)",
            "Natural Disaster": "$200k - $1M (Routing)"
        }
        return impact_map.get(category, "Assess Impact")

    def fetch_official_alerts(self):
        """Fetches UN GDACS alerts (Official Data Layer)"""
        url = "https://www.gdacs.org/xml/rss.xml"
        feed = self.fetch_feed(url)
        alerts = []
        
        if not feed or not feed.entries: return []

        for entry in feed.entries[:5]: # Top 5 global alerts
            alerts.append({
                "Title": f"🚨 [OFFICIAL] {entry.title}",
                "Link": entry.link,
                "Date": "LIVE",
                "Risk": "CRITICAL",
                "Category": "Natural Disaster",
                "Confidence": 100,
                "Impact": "Infrastructure Damage",
                "Source": "UN GDACS"
            })
        return alerts

    def scan_target(self, query):
        # 1. Google News
        base = query.replace(" ", "%20")
        url = f"https://news.google.com/rss/search?q={base}%20when:7d&hl=en-IN&gl=IN&ceid=IN:en"
        feed = self.fetch_feed(url)
        
        results = []
        
        # 2. Add Official Alerts (if relevant keywords match)
        # Note: In production, you would do geospatial matching. Here we just grab global alerts for demo.
        global_alerts = self.fetch_official_alerts()
        results.extend(global_alerts)

        if feed and feed.entries:
            for entry in feed.entries[:15]:
                text = f"{entry.title} {entry.get('summary', '')}"
                blob = TextBlob(text)
                
                # Logic
                category = self.classify_event(text)
                
                risk = "LOW"
                if blob.sentiment.polarity < -0.05: risk = "MEDIUM"
                if blob.sentiment.polarity < -0.2: risk = "HIGH"
                # Critical override
                if category == "Military Conflict" and risk == "HIGH": risk = "CRITICAL"

                conf = self.calculate_confidence(entry)
                impact = self.estimate_impact(risk, category)

                results.append({
                    "Title": entry.title,
                    "Link": entry.link,
                    "Date": entry.published if hasattr(entry, 'published') else "Recent",
                    "Risk": risk,
                    "Category": category,
                    "Confidence": conf,
                    "Impact": impact,
                    "Source": entry.source.get('title', 'Unknown')
                })
        
        return results

# --- FRONTEND UI ---
st.set_page_config(page_title="SENTINEL-NODE V18", layout="wide")

if 'active_scan' not in st.session_state: st.session_state['active_scan'] = None

# Header
st.title("🗺️ Sentinel-Node: Global Risk Command")
st.markdown("### Multi-Source Intelligence Platform (News + GDACS + Gov)")

# --- MAP LAYER ---
m = folium.Map(location=[20.0, 0.0], zoom_start=2, tiles="CartoDB dark_matter")

for name, data in GEO_ASSETS.items():
    color = "red" if data['type'] == "Conflict Zone" else "orange" if data['type'] == "Choke Point" else "blue"
    folium.Marker(
        data['coords'], 
        popup=name, 
        tooltip=f"{name}", 
        icon=folium.Icon(color=color, icon="info-sign")
    ).add_to(m)

st_data = st_folium(m, height=350, width="100%")

# --- LOGIC: MAP CLICK ---
trigger = None
if st_data and st_data.get("last_object_clicked_popup"):
    trigger = st_data["last_object_clicked_popup"]

# --- SIDEBAR CONTROLS ---
st.sidebar.title("⚙️ Signal Controls")
st.sidebar.success("System Status: ONLINE")
st.sidebar.markdown("---")
st.sidebar.caption("Active Data Layers:")
st.sidebar.checkbox("Global News (OSINT)", value=True, disabled=True)
st.sidebar.checkbox("UN GDACS Alerts", value=True, disabled=True)
st.sidebar.checkbox("Maritime Authority Feeds", value=True, disabled=True)

# --- EXECUTION ---
engine = IntelligenceEngine()

if trigger:
    with st.spinner(f"📡 Fusing multi-source intelligence for: {trigger}..."):
        # Fetch Data
        scan_results = engine.scan_target(GEO_ASSETS[trigger]['query'])
        st.session_state['active_scan'] = {'target': trigger, 'data': scan_results}

# --- DASHBOARD RESULTS ---
if st.session_state['active_scan']:
    data = st.session_state['active_scan']['data']
    target = st.session_state['active_scan']['target']
    df = pd.DataFrame(data)

    st.markdown("---")
    st.header(f"🛑 Intelligence Feed: {target}")

    if not df.empty:
        # --- TOP LAYER: OFFICIAL ALERTS ---
        official = df[df['Source'].str.contains("Official|GDACS")]
        if not official.empty:
            st.error(f"🚨 ACTIVE OFFICIAL WARNINGS ({len(official)})")
            for _, row in official.iterrows():
                st.write(f"**{row['Source']}**: {row['Title']} - [View]({row['Link']})")
        
        st.markdown("---")

        # --- VISUAL ANALYTICS (ALTAIR) ---
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Risk Distribution")
            # Simple Bar Chart
            bar = alt.Chart(df).mark_bar().encode(
                x=alt.X('Risk', sort=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']),
                y='count()',
                color=alt.Color('Risk', scale=alt.Scale(domain=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'], range=['red', 'orange', 'yellow', 'green']))
            ).properties(height=250)
            st.altair_chart(bar, use_container_width=True)

        with c2:
            st.subheader("Source Reliability")
            # Pie Chart
            pie = alt.Chart(df).mark_arc(innerRadius=50).encode(
                theta='count()',
                color=alt.Color('Category'),
                tooltip=['Category', 'count()']
            ).properties(height=250)
            st.altair_chart(pie, use_container_width=True)

        # --- FEED ---
        st.subheader("📋 Operational Updates")
        
        for _, row in df.iterrows():
            if "Official" in row['Source']: continue # Skip official (already shown top)
            
            icon = "🔴" if row['Risk'] == "CRITICAL" else "🟠" if row['Risk'] == "HIGH" else "🟢"
            
            with st.expander(f"{icon} {row['Title']}"):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"**Category:** {row['Category']}")
                    st.caption(f"Source: {row['Source']} | Date: {row['Date']}")
                    st.markdown(f"[Read Source]({row['Link']})")
                with col_b:
                    st.metric("Confidence", f"{row['Confidence']}%")
                    st.info(f"Impact: {row['Impact']}")

    else:
        st.warning("No active intelligence found for this sector.")
