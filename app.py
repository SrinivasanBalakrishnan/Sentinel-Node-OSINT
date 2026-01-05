import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import time

# --- CONFIGURATION (The Secret Sauce) ---
# This is where your expertise shines. You pick the "Choke Points".
TARGETS = {
    "Strait of Malacca": "Strait of Malacca OR Singapore Strait shipping",
    "Taiwan Strait": "Taiwan Strait military OR TSMC supply chain",
    "Suez Canal": "Suez Canal blocked OR Red Sea attacks",
    "Hormuz": "Strait of Hormuz oil tanker",
    "South China Sea": "South China Sea collision OR disputed waters"
}

# --- THE ENGINE ---
def fetch_risk_news(query):
    # We use Google News RSS (Free & Real-time)
    encoded_query = query.replace(" ", "%20")
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    
    news_items = []
    for entry in feed.entries[:5]: # Top 5 newest stories
        # AI SENTIMENT ANALYSIS
        analysis = TextBlob(entry.title + " " + entry.summary)
        sentiment_score = analysis.sentiment.polarity
        
        # Risk Logic: Negative sentiment = High Risk
        risk_level = "LOW"
        if sentiment_score < -0.1: risk_level = "MEDIUM"
        if sentiment_score < -0.3: risk_level = "HIGH"
        if "attack" in entry.title.lower() or "blocked" in entry.title.lower(): risk_level = "CRITICAL"

        news_items.append({
            "Title": entry.title,
            "Link": entry.link,
            "Published": entry.published,
            "Risk Score": risk_level,
            "Raw Sentiment": round(sentiment_score, 2)
        })
    return news_items

# --- THE DASHBOARD (Frontend) ---
st.set_page_config(page_title="SENTINEL-NODE: Hyper-Local Risk", layout="wide")

st.title("📡 SENTINEL-NODE: Critical Infrastructure Monitor")
st.markdown(f"*Live Intelligence Feed | Status: Online | {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
st.markdown("---")

# Sidebar for controls
st.sidebar.header("Target Sector")
filter_option = st.sidebar.selectbox("Select Choke Point", list(TARGETS.keys()))

if st.sidebar.button("Run Scan Now"):
    with st.spinner(f"Scanning vectors for {filter_option}..."):
        # Run the engine
        data = fetch_risk_news(TARGETS[filter_option])
        df = pd.DataFrame(data)

        # Display Metrics
        critical_count = df[df["Risk Score"] == "CRITICAL"].shape[0]
        st.metric(label="Critical Threats Detected", value=critical_count, delta_color="inverse")

        # Visual Alert System
        for index, row in df.iterrows():
            if row["Risk Score"] in ["CRITICAL", "HIGH"]:
                st.error(f"⚠️ {row['Risk Score']} RISK: {row['Title']}")
            elif row["Risk Score"] == "MEDIUM":
                st.warning(f"⚡ {row['Risk Score']} RISK: {row['Title']}")
            else:
                st.success(f"✅ {row['Risk Score']}: {row['Title']}")
            
            with st.expander("See Details"):
                st.write(f"**Source:** {row['Published']}")
                st.write(f"**AI Sentiment:** {row['Raw Sentiment']}")
                st.write(f"[Read Article]({row['Link']})")

st.sidebar.markdown("---")
st.sidebar.info("Built by [Your Name] | The Architecture of Dominion")
