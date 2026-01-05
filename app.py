import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
import time

# --- CONFIGURATION (Indo-Pacific Focus) ---
TARGETS = {
    "Strait of Malacca": "Strait of Malacca OR Singapore Strait shipping",
    "Taiwan Strait": "Taiwan Strait military OR TSMC supply chain",
    "Red Sea / Suez": "Red Sea attacks OR Suez Canal blocked OR Houthi",
    "South China Sea": "South China Sea collision OR Philippines coast guard",
    "Indian Ocean": "Indian Ocean navy OR Hambantota port OR Adani ports",
    "Semiconductor Supply": "TSMC Arizona OR Nvidia supply chain OR chip shortage"
}

# --- HELPER FUNCTIONS ---
def parse_date(date_str):
    """Attempts to parse RSS date formats into a clean YYYY-MM-DD string."""
    try:
        struct_time = feedparser._parse_date(date_str)
        return datetime(*struct_time[:6])
    except:
        return datetime.now()

def fetch_feed(query, days_back=1):
    """
    Fetches news with a specific time window.
    Google News Query Format: 'Topic when:Xd'
    """
    # URL Encoding the query safely
    base_query = query.replace(" ", "%20")
    
    # Force sorting by date using 'when:Xd'
    final_query = f"{base_query}%20when:{days_back}d"
    
    # We use 'ceid=IN:en' (India Edition) for better Indo-Pacific coverage
    url = f"https://news.google.com/rss/search?q={final_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    return feedparser.parse(url)

# --- THE ENGINE (24HR -> 7DAY FALLBACK) ---
def get_intel(target_name):
    query = TARGETS[target_name]
    
    # ATTEMPT 1: Strict 24-Hour Search
    feed = fetch_feed(query, days_back=1)
    items = feed.entries
    source_type = "⚡ Live Feed (Last 24 Hours)"

    # ATTEMPT 2: Fallback to 7 Days if 24h is empty
    if not items:
        feed = fetch_feed(query, days_back=7)
        items = feed.entries
        source_type = "📅 Extended Feed (Last 7 Days)"
    
    processed_data = []
    
    for entry in items[:20]: # Analyze top 20 items
        # 1. Clean Date
        pub_date_obj = parse_date(entry.published)
        pub_date_str = pub_date_obj.strftime("%Y-%m-%d")
        
        # 2. AI Sentiment Analysis
        # We analyze Title + Summary for better context
        text_to_analyze = f"{entry.title} {entry.get('summary', '')}"
        blob = TextBlob(text_to_analyze)
        sentiment = blob.sentiment.polarity # -1.0 to 1.0
        
        # 3. Risk Scoring Logic
        risk_score = "LOW"
        if sentiment < -0.05: risk_score = "MEDIUM"
        if sentiment < -0.2: risk_score = "HIGH"
        
        # 4. Keyword Overrides (The "Kill Switch")
        critical_words = ["attack", "missile", "sinking", "blocked", "collision", "suspended", "ban", "sanction", "drone"]
        if any(w in entry.title.lower() for w in critical_words):
            risk_score = "CRITICAL"
            
        processed_data.append({
            "Title": entry.title,
            "Link": entry.link,
            "Date": pub_date_str,
            "Risk": risk_score,
            "Sentiment": round(sentiment, 2),
            "Source": entry.source.get('title', 'Google News')
        })
        
    return processed_data, source_type

# --- FRONTEND (STREAMLIT) ---
st.set_page_config(page_title="SENTINEL-NODE V3", layout="wide")

st.title("📡 SENTINEL-NODE: Risk Command")
st.markdown("*Real-time Open Source Intelligence (OSINT) for Global Supply Chains*")
st.markdown("---")

# Sidebar
st.sidebar.header("Target Vector")
selected_target = st.sidebar.selectbox("Choose Choke Point", list(TARGETS.keys()))

if st.sidebar.button("Initialize Scan"):
    with st.spinner(f"Intercepting signals for {selected_target}..."):
        
        # Run Engine
        data, time_window = get_intel(selected_target)
        
        if not data:
            st.error("No intelligence found. Target is silent.")
        else:
            df = pd.DataFrame(data)
            
            # Dashboard Metrics
            # Note: We use the source_type variable to tell the user WHICH time window triggered
            if "24 Hours" in time_window:
                st.success(f"Source: {time_window}")
            else:
                st.warning(f"Source: {time_window} (No 24h news found)")
            
            crit_count = len(df[df['Risk'] == "CRITICAL"])
            high_count = len(df[df['Risk'] == "HIGH"])
            
            # KPIS
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("CRITICAL THREATS", crit_count, delta_color="inverse")
            kpi2.metric("HIGH RISK ALERTS", high_count, delta_color="inverse")
            kpi3.metric("ARTICLES SCANNED", len(df))
            
            st.markdown("### 🛑 Live Threat Feed")
            
            # Display Cards
            for _, row in df.iterrows():
                # Dynamic Styling
                if row['Risk'] == "CRITICAL":
                    box_color = "🔴"
                    st.error(f"{box_color} **CRITICAL:** {row['Title']}")
                elif row['Risk'] == "HIGH":
                    box_color = "🟠"
                    st.warning(f"{box_color} **HIGH:** {row['Title']}")
                elif row['Risk'] == "MEDIUM":
                    box_color = "🟡"
                    st.warning(f"{box_color} **MEDIUM:** {row['Title']}")
                else:
                    st.success(f"🟢 **STABLE:** {row['Title']}")
                
                with st.expander("Intelligence Details"):
                    st.write(f"**Published:** {row['Date']}")
                    st.write(f"**Source:** {row['Source']}")
                    st.write(f"**AI Score:** {row['Sentiment']}")
                    st.markdown(f"[>> Access Source Terminal]({row['Link']})")

st.sidebar.markdown("---")
st.sidebar.caption("System: Sentinel-Node V3.0 | Status: Active")
