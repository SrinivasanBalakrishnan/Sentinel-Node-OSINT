import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import altair as alt # Visualization
from transformers import pipeline # Hugging Face AI
import time
import random

# -- MOCK AUTH & ASSETS --
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

# --- AI CORE: HUGGING FACE LOADER ---
# We cache this resource so it doesn't reload on every click (Critical for performance)
@st.cache_resource
def load_classifier():
    # Using a DistilBERT model fine-tuned for MNLI (Zero-Shot capability)
    # This is lighter than BART-Large (~260MB vs 1.6GB)
    return pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")

# --- CORE ENGINE ---
class IntelligenceEngine:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (SentinelNode-AI)'}
        # Load the AI model
        self.classifier = load_classifier()
        # Define the Labels for the AI to choose from
        self.candidate_labels = ["Military Conflict", "Supply Chain Delay", "Regulatory Sanction", "Natural Disaster", "Business Deal"]

    def fetch_feed(self, url):
        return feedparser.parse(url)

    def build_url(self, query, time_window="7d"):
        base = query.replace(" ", "%20")
        return f"https://news.google.com/rss/search?q={base}%20when:{time_window}&hl=en-IN&gl=IN&ceid=IN:en"

    def classify_event_ai(self, text):
        """Uses DistilBERT to classify the event type contextually"""
        try:
            # We only use the first 100 chars to speed up CPU inference
            result = self.classifier(text[:200], self.candidate_labels)
            # Return the top label (highest score)
            return result['labels'][0], result['scores'][0]
        except:
            return "Unclassified", 0.0

    def estimate_impact(self, risk, category):
        if risk == "LOW": return "$0 - Minimal"
        impact_map = {
            "Military Conflict": "$10M - $100M (Insurance Risk)",
            "Supply Chain Delay": "$500k - $5M (Ops Cost)",
            "Regulatory Sanction": "$1M - $10M (Compliance)",
            "Natural Disaster": "$200k - $2M (Routing)",
            "Business Deal": "Opportunity (Positive)"
        }
        return impact_map.get(category, "$100k - $1M")

    def scan_target(self, target_name, query, time_mode):
        url = self.build_url(query, "7d" if time_mode == "Last 7 Days" else "1d")
        feed = self.fetch_feed(url)
        
        results = []
        
        # Limit to Top 15 items to prevent AI timeout on free cloud
        for entry in feed.entries[:15]:
            text = f"{entry.title} {entry.get('summary', '')}"
            blob = TextBlob(text)
            
            # 1. AI Classification (The Heavy Lifting)
            category, cat_score = self.classify_event_ai(text)
            
            # 2. Risk Logic
            risk = "LOW"
            if blob.sentiment.polarity < -0.1: risk = "MEDIUM"
            if blob.sentiment.polarity < -0.3: risk = "HIGH"
            
            # Contextual Override: If AI is 90% sure it's Conflict/Sanction, elevate risk
            if category in ["Military Conflict", "Regulatory Sanction"] and cat_score > 0.8:
                if risk == "MEDIUM": risk = "HIGH"
                if risk == "HIGH": risk = "CRITICAL"

            impact = self.estimate_impact(risk, category)

            results.append({
                "Title": entry.title,
                "Link": entry.link,
                "Date": entry.published if hasattr(entry, 'published') else "Recent",
                "Risk": risk,
                "Category": category,
                "AI_Score": round(cat_score, 2), # Confidence
                "Impact": impact,
                "Source": entry.source.get('title', 'Unknown')
            })
        
        return results

# --- FRONTEND INIT ---
st.set_page_config(page_title="SENTINEL-NODE V16 AI", layout="wide")

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_role' not in st.session_state: st.session_state['user_role'] = None
if 'active_scan' not in st.session_state: st.session_state['active_scan'] = None

# --- LOGIN ---
if not st.session_state['logged_in']:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.title("🔒 Sentinel-Node AI")
        st.caption("Enterprise Risk Intelligence Platform")
        user = st.text_input("Username (analyst/manager)")
        pwd = st.text_input("Password", type="password")
        if st.button("Access Dashboard"):
            if user in USERS and pwd == USERS[user]["pass"]:
                st.session_state['logged_in'] = True
                st.session_state['user_role'] = USERS[user]["role"]
                st.rerun()
            else: st.error("Access Denied")
    st.stop()

# --- MAIN DASHBOARD ---
st.sidebar.title(f"👤 {st.session_state['user_role']}")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()
st.sidebar.header("📡 Settings")
time_mode = st.sidebar.selectbox("Horizon", ["Last 24 Hours", "Last 7 Days"], index=1)

# Init Engine
# This triggers the model download on first run (takes a few seconds)
with st.spinner("Initializing Neural Core..."):
    engine = IntelligenceEngine()

st.title("🗺️ Global Risk Operating Picture")

# --- MAP ---
m = folium.Map(location=[20.0, 0.0], zoom_start=2, tiles="CartoDB dark_matter")
for name, data in GEO_ASSETS.items():
    color = "red" if data['type'] == "Conflict Zone" else "orange" if data['type'] == "Choke Point" else "blue"
    folium.Marker(
        location=data['coords'],
        popup=name,
        tooltip=f"{name}",
        icon=folium.Icon(color=color, icon="info-sign")
    ).add_to(m)

map_data = st_folium(m, height=350, width="100%")

trigger_target = None
if map_data and map_data.get("last_object_clicked_popup"):
    trigger_target = map_data["last_object_clicked_popup"]

# --- EXECUTION ---
if trigger_target:
    with st.spinner(f"⚡ AI Analyzing vector: {trigger_target}..."):
        results = engine.scan_target(trigger_target, GEO_ASSETS[trigger_target]['query'], time_mode)
        st.session_state['active_scan'] = {'target': trigger_target, 'data': results}

# --- ANALYTICS & VISUALIZATION LAYER ---
if st.session_state['active_scan']:
    data = st.session_state['active_scan']['data']
    target = st.session_state['active_scan']['target']
    df = pd.DataFrame(data)
    
    st.markdown("---")
    st.header(f"📊 Executive Analytics: {target}")
    
    if not df.empty:
        # --- ALTAIR CHARTS ---
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Risk Distribution")
            # Bar Chart: Count of Risks
            chart_risk = alt.Chart(df).mark_bar().encode(
                x=alt.X('Risk', sort=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']),
                y='count()',
                color=alt.Color('Risk', scale=alt.Scale(domain=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'], range=['red', 'orange', 'yellow', 'green']))
            ).properties(height=300)
            st.altair_chart(chart_risk, use_container_width=True)
            
        with c2:
            st.subheader("Root Cause Taxonomy")
            # Donut Chart: Categories
            chart_cat = alt.Chart(df).mark_arc(innerRadius=50).encode(
                theta='count()',
                color='Category',
                tooltip=['Category', 'count()']
            ).properties(height=300)
            st.altair_chart(chart_cat, use_container_width=True)

        # --- FEED ---
        st.subheader("🛑 AI-Classified Threat Feed")
        for _, row in df.iterrows():
            icon = "🔴" if row['Risk'] == "CRITICAL" else "🟠" if row['Risk'] == "HIGH" else "🟢"
            with st.expander(f"{icon} [{row['Risk']}] {row['Title']}"):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"**AI Classification:** {row['Category']} (Confidence: {int(row['AI_Score']*100)}%)")
                    st.caption(f"Source: {row['Source']}")
                with col_b:
                    st.info(f"Impact: {row['Impact']}")
                    st.markdown(f"[View]({row['Link']})")
    else:
        st.warning("No data found.")
