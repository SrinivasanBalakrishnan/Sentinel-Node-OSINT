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
    "Red Sea / Suez": "Red Sea attacks OR Suez Canal blocked OR Houthi",
    "South China Sea": "South China Sea collision OR Philippines coast guard",
    "Indian Ocean": "Indian Ocean navy OR Hambantota port OR Adani ports",
    "Semiconductor Supply": "TSMC Arizona OR Nvidia supply chain OR chip shortage"
}

# Map User Selection to Google News URL Parameters
TIME_FILTERS = {
    "Last 1 Hour": "1h",
    "Last 24 Hours": "1d",
    "Last 7 Days": "7d",
    "Past 1 Month": "1m",
    "Past 1 Year": "1y",
    "Historical (5 Years)": "5y"
}

# --- HELPER FUNCTIONS ---
def parse_date(date_str):
    try:
        struct_time = feedparser._parse_date(date_str)
        return datetime(*struct_time[:6])
    except:
        return datetime.now()

def fetch_feed(query, time_param):
    """
    Fetches news with a specific time window.
    """
    # URL Encoding
    base_query = query.replace(" ", "%20")
    
    # Construct the strictly filtered query
    # Syntax: topic when:1h (for 1 hour), when:1d (for 1 day), etc.
    final_query = f"{base_query}%20when:{time_param}"
    
    # We use 'ceid=IN:en' for Indo-Pacific context
    url = f"https://news.google.com/rss/search?q={final_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    return feedparser.parse(url)

# --- THE ENGINE ---
def get_intel(target_name, time_selection):
    query = TARGETS[target_name]
    time_code = TIME_FILTERS[time_selection]
    
    # Fetch Data
    feed = fetch_feed(query, time_code)
    items = feed.entries
    
    processed_data = []
    
    for entry in items[:20]: # Analyze top 20 items
        # 1. Clean Date
        pub_date_obj = parse_date(entry.published)
        pub_date_str = pub_date_obj.strftime("%Y-%m-%d")
        
        # 2. AI Sentiment
        text_to_analyze = f"{entry.title} {entry.get('summary', '')}"
        blob = TextBlob(text_to_analyze)
        sentiment = blob.sentiment.polarity
        
        # 3. Risk Scoring
        risk_score = "LOW"
        if sentiment < -0.05: risk_score = "MEDIUM"
        if sentiment < -0.2: risk_score = "HIGH"
        
        # 4. Critical Keyword Override
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
        
    return processed_data

# --- FRONTEND ---
st.set_page_config(page_title="SENTINEL-NODE V4", layout="wide")

# Top Layout: Title on Left, Time Filter on Right
col1, col2 = st.columns([3, 1])

with col1:
    st.title("📡 SENTINEL-NODE: Risk Command")
    st.markdown("*Real-time Open Source Intelligence (OSINT)*")

with col2:
    # THE NEW DROPDOWN (Top Right)
    st.write("### ⏳ Time Filter")
    selected_time = st.selectbox("Select Window", list(TIME_FILTERS.keys()), index=1) # Default to 24h

st.markdown("---")

# Main Interface
c1, c2 = st.columns([1, 3])

with c1:
    st.header("Target Vector")
    selected_target = st.radio("Choose Choke Point", list(TARGETS.keys()))
    
    st.markdown("---")
    if st.button("Initialize Scan", type="primary", use_container_width=True):
        
        with st.spinner(f"Scanning {selected_target} for {selected_time}..."):
            data = get_intel(selected_target, selected_time)
            
            if not data:
                st.error(f"No intelligence found for **{selected_target}** in **{selected_time}**.")
            else:
                # Store data in session state so it doesn't disappear
                st.session_state['data'] = data
                st.session_state['target'] = selected_target

# Results Area (Right Column)
with c2:
    if 'data' in st.session_state:
        df = pd.DataFrame(st.session_state['data'])
        
        # Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric("ARTICLES FOUND", len(df))
        m2.metric("CRITICAL THREATS", len(df[df['Risk'] == "CRITICAL"]))
        m3.metric("SOURCE WINDOW", selected_time)
        
        st.markdown("### 🛑 Threat Feed")
        
        for _, row in df.iterrows():
            if row['Risk'] == "CRITICAL":
                st.error(f"🔴 **CRITICAL:** {row['Title']}")
            elif row['Risk'] == "HIGH":
                st.warning(f"🟠 **HIGH:** {row['Title']}")
            elif row['Risk'] == "MEDIUM":
                st.warning(f"🟡 **MEDIUM:** {row['Title']}")
            else:
                st.success(f"🟢 **STABLE:** {row['Title']}")
                
            with st.expander("Intelligence Details"):
                st.write(f"**Date:** {row['Date']} | **Source:** {row['Source']}")
                st.markdown(f"[Read Article]({row['Link']})")
    else:
        st.info("👈 Select a target and click 'Initialize Scan' to begin.")

st.sidebar.caption("System: Sentinel-Node V4.0 | Status: Active")
