import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
import time

# --- CONFIGURATION ---
TARGETS = {
    "Strait of Malacca": '"Strait of Malacca" OR "Singapore Strait" OR "Malacca Strait"',
    "Taiwan Strait": '"Taiwan Strait" OR "PLA navy" OR "TSMC" OR "Taiwan defense"',
    "Red Sea / Suez": '"Red Sea" OR "Suez Canal" OR "Houthi" OR "Bab el-Mandeb"',
    "South China Sea": '"South China Sea" OR "Spratly Islands" OR "Second Thomas Shoal"',
    "Indian Ocean": '"Indian Ocean" OR "Hambantota port" OR "Diego Garcia" OR "Andaman Sea"',
    "Semiconductor Supply": '"TSMC" OR "Nvidia" OR "Foxconn" OR "semiconductor supply chain"'
}

EXCLUDED_TERMS = [
    "Ukraine", "Russia", "Kyiv", "Moscow", "Putin", "Zelensky", 
    "Gaza", "Hamas", "Israel", "Palestin", 
    "Venezuela", "Caracas", "Maduro",
    "Football", "Cricket", "Movie", "Celeb"
]

# --- HELPER FUNCTIONS ---
def parse_date(date_str):
    try:
        struct_time = feedparser._parse_date(date_str)
        return datetime(*struct_time[:6])
    except:
        return datetime.now()

def get_date_string(days_ago):
    """Returns a date string YYYY-MM-DD for X days ago."""
    d = datetime.now() - timedelta(days=days_ago)
    return d.strftime("%Y-%m-%d")

def fetch_rss_url(query, after_date=None, before_date=None, when_param=None):
    base_query = query.replace(" ", "%20")
    
    # Logic: Use 'after/before' for precise slicing, or 'when' for simple ranges
    if after_date and before_date:
        final_query = f"{base_query}+after:{after_date}+before:{before_date}"
    elif when_param:
        final_query = f"{base_query}%20when:{when_param}"
    else:
        final_query = base_query

    # We use 'ceid=IN:en' for Indo-Pacific context
    return f"https://news.google.com/rss/search?q={final_query}&hl=en-IN&gl=IN&ceid=IN:en"

# --- THE DEEP DIVE ENGINE ---
def get_intel_deep_dive(target_name, time_mode):
    query = TARGETS[target_name]
    all_feeds = []

    # STRATEGY 1: SIMPLE FETCH (For short durations)
    if time_mode in ["Last 1 Hour", "Last 24 Hours", "Last 7 Days"]:
        map_time = {"Last 1 Hour": "1h", "Last 24 Hours": "1d", "Last 7 Days": "7d"}
        url = fetch_rss_url(query, when_param=map_time[time_mode])
        all_feeds.append(feedparser.parse(url))

    # STRATEGY 2: TIME SLICING (For "Past 1 Month" -> Break into 3 weeks)
    elif time_mode == "Past 1 Month (Deep Dive)":
        # Slice 1: Day 0-7
        url1 = fetch_rss_url(query, when_param="7d")
        # Slice 2: Day 8-14
        url2 = fetch_rss_url(query, after_date=get_date_string(14), before_date=get_date_string(7))
        # Slice 3: Day 15-30
        url3 = fetch_rss_url(query, after_date=get_date_string(30), before_date=get_date_string(14))
        
        # Parallel fetch simulation (sequential for simplicity)
        all_feeds = [feedparser.parse(url1), feedparser.parse(url2), feedparser.parse(url3)]

    # STRATEGY 3: HISTORICAL ARCHIVE
    elif time_mode == "Past 1 Year":
        # Just grab the 'Best Match' for the year
        url = fetch_rss_url(query, when_param="365d")
        all_feeds.append(feedparser.parse(url))

    # --- PROCESS & MERGE ---
    processed_data = []
    seen_titles = set()

    for feed in all_feeds:
        for entry in feed.entries:
            # Noise Filter
            if any(term.lower() in entry.title.lower() for term in EXCLUDED_TERMS):
                continue
            
            # Deduplication
            if entry.title.lower() in seen_titles:
                continue
            seen_titles.add(entry.title.lower())

            pub_date_obj = parse_date(entry.published)
            pub_date_str = pub_date_obj.strftime("%Y-%m-%d")

            # Sentiment
            text_to_analyze = f"{entry.title} {entry.get('summary', '')}"
            blob = TextBlob(text_to_analyze)
            sentiment = blob.sentiment.polarity
            
            risk_score = "LOW"
            if sentiment < -0.05: risk_score = "MEDIUM"
            if sentiment < -0.2: risk_score = "HIGH"
            
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

    df = pd.DataFrame(processed_data)
    if not df.empty:
        # Sort by Date Descending
        df = df.sort_values(by=['Date'], ascending=False)
        
    return df

# --- FRONTEND ---
st.set_page_config(page_title="SENTINEL-NODE V10", layout="wide")

if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 0

# Sidebar
st.sidebar.title("⚙️ Mission Control")
selected_target = st.sidebar.radio("Target Vector", list(TARGETS.keys()))

st.sidebar.markdown("---")
st.sidebar.info("ℹ️ **Deep Dive Mode:** 'Past 1 Month' now performs 3 separate scans (Week 1, Week 2, Week 3-4) to force Google to reveal older data.")

# Main Layout
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("📡 SENTINEL-NODE: Risk Command")
    st.markdown("*Real-time Open Source Intelligence (OSINT)*")

with col2:
    st.write("### ⏳ Time Mode")
    # UPDATED OPTIONS
    time_options = ["Last 24 Hours", "Last 7 Days", "Past 1 Month (Deep Dive)", "Past 1 Year"]
    selected_time = st.selectbox("Select Window", time_options, index=1)

with col3:
    st.write("### 🎚️ Threat Level")
    threat_filter = st.selectbox("Show Only", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"], index=0)

st.markdown("---")

if st.button("🚀 INITIALIZE DEEP SCAN", type="primary", use_container_width=True):
    st.session_state['page_number'] = 0 
    with st.spinner(f"Executing Multi-Vector Scan for {selected_target}..."):
        df_result = get_intel_deep_dive(selected_target, selected_time)
        
        if df_result.empty:
            st.error("No intelligence found.")
            st.session_state['data'] = None
        else:
            st.session_state['data'] = df_result.to_dict('records')
            st.session_state['target'] = selected_target

# Results
if 'data' in st.session_state and st.session_state['data'] is not None:
    df = pd.DataFrame(st.session_state['data'])
    
    if threat_filter != "All":
        df = df[df['Risk'] == threat_filter]
    
    total_items = len(df)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("INTEL MATCHED", total_items)
    if not df.empty:
        m2.metric("CRITICAL THREATS", len(df[df['Risk'] == "CRITICAL"]))
    m3.metric("SCAN MODE", selected_time)
    
    st.markdown(f"### 🛑 Threat Feed")

    if df.empty:
        st.warning(f"No events found matching threat level: **{threat_filter}**")
    else:
        if 'items_per_page' not in st.session_state:
            st.session_state['items_per_page'] = 5

        items_per_page = st.session_state['items_per_page']
        total_pages = max(1, (total_items // items_per_page) + (1 if total_items % items_per_page > 0 else 0))
        
        if st.session_state['page_number'] >= total_pages:
            st.session_state['page_number'] = 0
        
        current_page = st.session_state['page_number']
        start_idx = current_page * items_per_page
        end_idx = start_idx + items_per_page
        page_data = df.iloc[start_idx:end_idx]

        for _, row in page_data.iterrows():
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
                st.write(f"**AI Risk Score:** {row['Sentiment']}")
                st.markdown(f"[Read Article]({row['Link']})")

        st.markdown("---")
        
        b1, b2, b3, b4 = st.columns([1, 2, 1, 1])
        
        with b1:
            if st.button("⬅️ Previous"):
                if st.session_state['page_number'] > 0:
                    st.session_state['page_number'] -= 1
                    st.rerun()
        
        with b2:
            st.markdown(f"<div style='text-align: center; padding-top: 10px;'>Page <b>{current_page + 1}</b> of <b>{total_pages}</b></div>", unsafe_allow_html=True)
        
        with b3:
            if st.button("Next ➡️"):
                if st.session_state['page_number'] < total_pages - 1:
                    st.session_state['page_number'] += 1
                    st.rerun()
        
        with b4:
            def update_items():
                st.session_state['items_per_page'] = st.session_state.new_items
                st.session_state['page_number'] = 0 

            st.selectbox(
                "Rows:", 
                options=[5, 10, 25, 50], 
                index=0,
                key="new_items",
                on_change=update_items,
                label_visibility="collapsed"
            )

else:
    st.info("👈 Select a target and click 'Initialize Scan'.")
