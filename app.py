import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
import concurrent.futures
import folium
from streamlit_folium import st_folium
import re
import random
import time

# --- MOCK AUTHENTICATION & RBAC (Category 5) ---
USERS = {
    "analyst": {"role": "Analyst", "pass": "admin"},
    "manager": {"role": "Risk Manager", "pass": "admin"},
    "exec": {"role": "Executive", "pass": "admin"}
}

# --- CONFIGURATION: GEOSPATIAL DATABASE (Category 3) ---
# Now includes 'Type' for icon selection
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

# --- INTELLIGENCE TAXONOMY (Category 1 & 4) ---
# Better than simple keywords: Regex patterns for Root Cause Analysis
EVENT_TAXONOMY = {
    "Conflict": [r"\bmissile\b", r"\bdrone strike\b", r"\bnavy\b", r"\bwarship\b", r"\battack\b"],
    "Logistics": [r"\bblocked\b", r"\bgrounded\b", r"\bsuspended\b", r"\bcongestion\b", r"\bdelay\b"],
    "Regulatory": [r"\bsanction\b", r"\bseized\b", r"\bban\b", r"\btariff\b", r"\bcustoms\b"],
    "Nature": [r"\bcyclone\b", r"\btyphoon\b", r"\bearthquake\b", r"\btsunami\b", r"\bfog\b"]
}

# --- CORE ENGINE CLASS (Enterprise Structure) ---
class IntelligenceEngine:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (SentinelNode-Enterprise)'}

    def fetch_feed(self, url):
        return feedparser.parse(url)

    def build_url(self, query, time_window="7d"):
        base = query.replace(" ", "%20")
        return f"https://news.google.com/rss/search?q={base}%20when:{time_window}&hl=en-IN&gl=IN&ceid=IN:en"

    def classify_event(self, text):
        """Determines Root Cause using Regex Taxonomy"""
        text = text.lower()
        detected_categories = []
        
        for category, patterns in EVENT_TAXONOMY.items():
            for pat in patterns:
                if re.search(pat, text):
                    detected_categories.append(category)
                    break # One hit per category is enough
        
        return detected_categories if detected_categories else ["Unclassified"]

    def calculate_confidence(self, entry, risk_score):
        """Generates a pseudo-confidence score (0-100%)"""
        # Logic: High risk + reliable source + recent = High Confidence
        base_score = 50
        
        # Source Credibility (Mock List)
        reliable_sources = ["Reuters", "Bloomberg", "Al Jazeera", "BBC", "Maritime Executive"]
        source = entry.source.get('title', '')
        if any(s in source for s in reliable_sources):
            base_score += 20
            
        # Recency
        try:
            pub = datetime(*entry.published_parsed[:6])
            if (datetime.now() - pub).days < 2:
                base_score += 15
        except: pass

        return min(base_score, 95)

    def estimate_impact(self, risk, category):
        """Simulates Business Impact Quantification (Category 6)"""
        if risk == "LOW": return "$0 - Minimal"
        
        impact_map = {
            "Conflict": "$5M - $50M (Insurance Spike)",
            "Logistics": "$500k - $5M (Delay Costs)",
            "Regulatory": "$1M - $10M (Compliance Risk)",
            "Nature": "$200k - $2M (Routing Deviation)"
        }
        
        base = impact_map.get(category[0], "$100k - $1M")
        if risk == "CRITICAL": base = base.replace("$", "$$").upper() + " 🚨"
        return base

    def scan_target(self, target_name, query, time_mode):
        url = self.build_url(query, "7d" if time_mode == "Last 7 Days" else "1d")
        feed = self.fetch_feed(url)
        
        results = []
        max_risk_level = 0 # 0=Low, 1=Med, 2=High, 3=Crit

        for entry in feed.entries:
            # 1. Text Analysis
            text = f"{entry.title} {entry.get('summary', '')}"
            blob = TextBlob(text)
            
            # 2. Event Classification (Root Cause)
            categories = self.classify_event(text)
            
            # 3. Risk Logic (Weighted)
            risk = "LOW"
            score = 0
            if blob.sentiment.polarity < -0.1: risk, score = "MEDIUM", 1
            if blob.sentiment.polarity < -0.3: risk, score = "HIGH", 2
            
            # Critical Override (Regex based)
            is_critical = "Conflict" in categories or "Regulatory" in categories
            if is_critical and score >= 1: 
                risk, score = "CRITICAL", 3

            max_risk_level = max(max_risk_level, score)

            # 4. Confidence & Impact
            conf = self.calculate_confidence(entry, risk)
            impact = self.estimate_impact(risk, categories)

            results.append({
                "Title": entry.title,
                "Link": entry.link,
                "Date": entry.published if hasattr(entry, 'published') else "Unknown",
                "Risk": risk,
                "Categories": categories,
                "Confidence": conf,
                "Impact": impact,
                "Source": entry.source.get('title', 'Unknown')
            })
        
        return results, max_risk_level

# --- FRONTEND: SESSION STATE INIT ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_role' not in st.session_state: st.session_state['user_role'] = None
if 'audit_log' not in st.session_state: st.session_state['audit_log'] = [] # Category 5
if 'active_scan' not in st.session_state: st.session_state['active_scan'] = None

# --- UI: LOGIN SCREEN ---
st.set_page_config(page_title="SENTINEL-NODE Enterprise", layout="wide")

if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.title("🔒 Sentinel-Node")
        st.markdown("### Enterprise Risk Platform")
        user = st.text_input("Username (Try: analyst, manager, exec)")
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            if user in USERS and pwd == USERS[user]["pass"]:
                st.session_state['logged_in'] = True
                st.session_state['user_role'] = USERS[user]["role"]
                st.rerun()
            else:
                st.error("Invalid Credentials")
    st.stop() # Halt app here if not logged in

# --- UI: MAIN DASHBOARD ---
st.sidebar.title(f"👤 {st.session_state['user_role']}")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📡 Command Center")
time_mode = st.sidebar.selectbox("Time Horizon", ["Last 24 Hours", "Last 7 Days"], index=1)

# Initialize Engine
engine = IntelligenceEngine()

st.title("🗺️ Global Risk Operating Picture")

# --- MAP LAYER (Category 2: Dynamic Markers) ---
# We use a Folium map where markers are colored by 'Type' (Mocking dynamic risk for now)
m = folium.Map(location=[20.0, 0.0], zoom_start=2, tiles="CartoDB dark_matter")

for name, data in GEO_ASSETS.items():
    # Visual Coding by Asset Type
    icon_color = "blue"
    if data['type'] == "Conflict Zone": icon_color = "red"
    elif data['type'] == "Choke Point": icon_color = "orange"
    
    folium.Marker(
        location=data['coords'],
        popup=name, # THIS is the key for click detection
        tooltip=f"{name} ({data['type']})",
        icon=folium.Icon(color=icon_color, icon="info-sign")
    ).add_to(m)

# Capture Click
st.markdown("### Select an Asset to Initialize Scan")
map_data = st_folium(m, height=400, width="100%")

# --- LOGIC: CLICK HANDLER (Category 2 Fix) ---
trigger_target = None

# The magic fix: Detect click by popup text (Name), not coordinates
if map_data and map_data.get("last_object_clicked_popup"):
    clicked_name = map_data["last_object_clicked_popup"]
    if clicked_name in GEO_ASSETS:
        trigger_target = clicked_name

# --- EXECUTION ENGINE ---
if trigger_target:
    asset_data = GEO_ASSETS[trigger_target]
    
    # Audit Log (Category 5)
    log_entry = f"{datetime.now().strftime('%H:%M:%S')} - User {st.session_state['user_role']} scanned {trigger_target}"
    st.session_state['audit_log'].append(log_entry)
    
    with st.spinner(f"⚡ Establishing uplinks to {trigger_target}..."):
        # Run Scan
        results, severity = engine.scan_target(trigger_target, asset_data['query'], time_mode)
        st.session_state['active_scan'] = {'target': trigger_target, 'data': results, 'severity': severity}

# --- RESULTS DASHBOARD ---
if st.session_state['active_scan']:
    data = st.session_state['active_scan']['data']
    target = st.session_state['active_scan']['target']
    
    st.markdown("---")
    
    # Header
    c1, c2 = st.columns([3, 1])
    with c1: st.header(f"🛑 Intelligence Brief: {target}")
    with c2: 
        # Export Button (Category 5)
        st.download_button("📥 Export JSON", data=str(data), file_name=f"{target}_intel.json")

    if not data:
        st.warning("No active signals detected in this sector.")
    else:
        # Convert to DF
        df = pd.DataFrame(data)
        
        # High-Level Metrics (Category 6)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Signals Intercepted", len(df))
        m2.metric("Critical Threats", len(df[df['Risk'] == "CRITICAL"]))
        
        # Calculate Avg Confidence
        avg_conf = df['Confidence'].mean()
        m3.metric("Signal Confidence", f"{int(avg_conf)}%")
        
        # Primary Root Cause
        top_cause = df['Categories'].explode().mode()
        m4.metric("Primary Driver", top_cause[0] if not top_cause.empty else "N/A")

        # Threat Feed
        st.subheader("⚠️ Live Threat Matrix")
        
        for _, row in df.iterrows():
            # color coding card
            card_color = "🟢"
            if row['Risk'] == "MEDIUM": card_color = "🟡"
            if row['Risk'] == "HIGH": card_color = "🟠"
            if row['Risk'] == "CRITICAL": card_color = "🔴"
            
            with st.expander(f"{card_color} [{row['Risk']}] {row['Title']}"):
                c_a, c_b = st.columns([2, 1])
                with c_a:
                    st.markdown(f"**Root Cause:** {', '.join(row['Categories'])}")
                    st.markdown(f"**Source:** {row['Source']} | **Date:** {row['Date']}")
                    st.markdown(f"[>> Verify Source]({row['Link']})")
                with c_b:
                    st.metric("Confidence", f"{row['Confidence']}%")
                    st.info(f"📉 Est. Impact: {row['Impact']}")

# --- AUDIT LOG DRAWER (Category 5) ---
with st.sidebar.expander("📜 System Audit Log"):
    for log in reversed(st.session_state['audit_log']):
        st.caption(log)
