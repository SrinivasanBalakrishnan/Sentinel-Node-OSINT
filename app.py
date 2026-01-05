import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import time

# --- CONFIGURATION ---
TARGETS = {
    "Strait of Malacca": "Strait of Malacca OR Singapore Strait shipping",
    "Taiwan Strait": "Taiwan Strait military OR TSMC supply chain",
    "Suez Canal": "Suez Canal blocked OR Red Sea attacks",
    "Hormuz": "Strait of Hormuz oil tanker",
    "South China Sea": "South China Sea collision OR disputed waters"
}

# --- THE ENGINE (UPDATED FOR REAL-TIME) ---
def fetch_risk_news(query):
    # We add '+when:7d' to force Google to give us news ONLY from the last 7 days
    # We also use 'sort=date' logic via the query structure
    encoded_query = query.replace(" ", "%20") + "+when:7d"
    
    # URL construction
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    # Parse the feed
    feed = feedparser.parse(url)
    
    news_items = []
    # If no news found, return empty
    if not feed.entries:
        return []

    for entry in feed.entries[:10]: # Increased to Top 10 stories
        # AI SENTIMENT ANALYSIS
        analysis = TextBlob(entry.title + " " + entry.summary)
        sentiment_score = analysis.sentiment.polarity
        
        # Risk Logic
        risk_level = "LOW"
        if sentiment_score < -0.1: risk_level = "MEDIUM"
        if sentiment_score < -0.3: risk_level = "HIGH"
        
        # KEYWORD OVERRIDE (The "Kill Words")
        critical_keywords = ["attack", "blocked", "closed", "sanction", "collision", "fired", "missile"]
        if any(word in entry.title.lower() for word in critical_keywords):
            risk_level = "CRITICAL"

        # Format Date (Clean up the messy RSS date format)
        try:
            # Try to make the date readable
            published_struct = entry.published_parsed
            published_date = time.strftime("%Y-%m-%d", published_struct)
        except:
            published_date = entry.published

        news_items.append({
            "Title": entry.title,
            "Link": entry.link,
            "Published": published_date,
            "Risk Score": risk_level,
            "Raw Sentiment": round(sentiment_score, 2)
        })
    return news_items

# --- THE DASHBOARD ---
st.set_page_config(page_title="SENTINEL-NODE: Hyper-Local Risk", layout="wide")

st.title("📡 SENTINEL-NODE: Critical Infrastructure Monitor")
st.markdown(f"*Live Intelligence Feed (Last 7 Days) | Status: Online | {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
st.markdown("---")

# Sidebar
st.sidebar.header("Target Sector")
filter_option = st.sidebar.selectbox("Select Choke Point", list(TARGETS.keys()))

if st.sidebar.button("Run Scan Now"):
    with st.spinner(f"Scanning vectors for {filter_option}..."):
        data = fetch_risk_news(TARGETS[filter_option])
        
        if not data:
            st.warning("No recent news found for this sector in the last 7 days.")
        else:
            df = pd.DataFrame(data)

            # Metrics
            critical_count = df[df["Risk Score"] == "CRITICAL"].shape[0]
            high_count = df[df["Risk Score"] == "HIGH"].shape[0]
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Critical Threats", critical_count, delta_color="inverse")
            col2.metric("High Risks", high_count, delta_color="inverse")
            col3.metric("Total Intel Inputs", len(df))

            st.markdown("### 🚨 Live Threat Matrix")
            
            # Visual Alert System
            for index, row in df.iterrows():
                # Define color based on risk
                if row["Risk Score"] == "CRITICAL":
                    icon = "🔴"
                    alert_type = st.error
                elif row["Risk Score"] == "HIGH":
                    icon = "🟠"
                    alert_type = st.warning
                elif row["Risk Score"] == "MEDIUM":
                    icon = "🟡"
                    alert_type = st.warning
                else:
                    icon = "🟢"
                    alert_type = st.success
                
                # Render the alert
                with st.expander(f"{icon} {row['Risk Score']}: {row['Title']} ({row['Published']})"):
                    st.write(f"**AI Sentiment Score:** {row['Raw Sentiment']}")
                    st.write(f"[Read Source Article]({row['Link']})")

st.sidebar.markdown("---")
st.sidebar.info("Built by [Your Name] | The Architecture of Dominion")
