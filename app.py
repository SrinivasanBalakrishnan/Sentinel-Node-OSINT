import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import time

# --- CONFIGURATION (STRICT QUERY MODE) ---
TARGETS = {
    "Strait of Malacca": '"Strait of Malacca" OR "Singapore Strait" OR "Malacca Strait"',
    "Taiwan Strait": '"Taiwan Strait" OR "PLA navy" OR "TSMC" OR "Taiwan defense"',
    "Red Sea / Suez": '"Red Sea" OR "Suez Canal" OR "Houthi" OR "Bab el-Mandeb"',
    "South China Sea": '"South China Sea" OR "Spratly Islands" OR "Second Thomas Shoal"',
    "Indian Ocean": '"Indian Ocean" OR "Hambantota port" OR "Diego Garcia" OR "Andaman Sea"',
    "Semiconductor Supply": '"TSMC" OR "Nvidia" OR "Foxconn" OR "semiconductor supply chain"'
}

# --- NOISE FILTER ---
EXCLUDED_TERMS = [
    "Ukraine", "Russia", "Kyiv", "Moscow", "Putin", "Zelensky", 
    "Gaza", "Hamas", "Israel", "Palestin", 
    "Venezuela", "Caracas", "Maduro",
    "Football", "Cricket", "Movie", "Celeb"
]

# --- FIX: GOOGLE RSS ONLY ACCEPTS DAYS (d) AND HOURS (h) ---
TIME_FILTERS = {
    "Last 1 Hour": "1h",
    "Last 24 Hours": "1d",
    "Last 7 Days": "7d",
    "Past 1 Month": "30d",   # Fixed: Changed 1m to 30d
    "Past 1 Year": "365d"    # Fixed: Changed 1y to 365d
}

# --- HELPER FUNCTIONS ---
def parse_date(date_str):
    try:
        struct_time = feedparser._parse_date(date_str)
        return datetime(*struct_time[:6])
    except:
        return datetime.now()

def fetch_feed(query, time_param):
    base_query = query.replace(" ", "%20")
    # We add quotes to time param to ensure stability
    final_query = f"{base_query}%20when:{time_param}"
    url = f"https://news.google.com/rss/search?q={final_query}&hl=en-IN&gl=IN&ceid=IN:en"
    return feedparser.parse(url)

# --- THE ENGINE ---
def get_intel(target_name, time_selection):
    query = TARGETS[target_name]
    time_code = TIME_FILTERS[time_selection]
    
    feed = fetch_feed(query, time_code)
    items = feed.entries
    
    processed_data = []
    
    for entry in items: 
        # LAYER 1: NOISE FILTER
        title_lower = entry.title.lower()
        if any(term.lower() in title_lower for term in EXCLUDED_TERMS):
            continue 

        pub_date_obj = parse_date(entry.published)
        pub_date_str = pub_date_obj.strftime("%Y-%m-%d")
        
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
        df = df.sort_values(by=['Sentiment'], ascending=True)
        
    return df

# --- FRONTEND ---
st.set_page_config(page_title="SENTINEL-NODE V8 (Stable)", layout="wide")

if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 0

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("📡 SENTINEL-NODE: Risk Command")
    st.markdown("*Real-time Open Source Intelligence (OSINT)*")

with col2:
    st.write("### ⏳ Time Filter")
    selected_time = st.selectbox("Select Window", list(TIME_FILTERS.keys()), index=2, key="time_select")

with col3:
    st.write("### 🎚️ Threat Level")
    threat_filter = st.selectbox("Show Only", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"], index=0)

st.markdown("---")

c1, c2 = st.columns([1, 3])

with c1:
    st.header("Target Vector")
    selected_target = st.radio("Choose Choke Point", list(TARGETS.keys()))
    
    st.markdown("---")
    st.info("ℹ️ **Note:** Filters active. Articles mentioning 'Ukraine', 'Russia', or 'Gaza' are automatically removed.")
    
    if st.button("Initialize Scan", type="primary", use_container_width=True):
        st.session_state['page_number'] = 0 
        with st.spinner(f"Scanning {selected_target}..."):
            df_result = get_intel(selected_target, selected_time)
            
            if df_result.empty:
                st.error("No intelligence found.")
                st.session_state['data'] = None
            else:
                st.session_state['data'] = df_result.to_dict('records')
                st.session_state['target'] = selected_target

# Results Area
with c2:
    if 'data' in st.session_state and st.session_state['data'] is not None:
        df = pd.DataFrame(st.session_state['data'])
        
        if threat_filter != "All":
            df = df[df['Risk'] == threat_filter]
        
        total_items = len(df)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("INTEL MATCHED", total_items)
        if not df.empty:
            m2.metric("CRITICAL THREATS", len(df[df['Risk'] == "CRITICAL"]))
        m3.metric("SOURCE WINDOW", selected_time)
        
        st.markdown(f"### 🛑 Threat Feed: {threat_filter} Events")

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
        st.info("👈 Select a target and click 'Initialize Scan' to begin.")

st.sidebar.caption("System: Sentinel-Node V8.0 | Status: Stable")
