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
    base_query = query.replace(" ", "%20")
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
    
    # FETCH ALL AVAILABLE (Up to 100 is standard RSS limit)
    for entry in items: 
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
    
    # SORTING LOGIC: Sort by Sentiment (Ascending) -> Most Negative/Critical First
    # If sentiments are equal, sort by Date (Newest First)
    df = pd.DataFrame(processed_data)
    if not df.empty:
        df = df.sort_values(by=['Sentiment'], ascending=True)
        
    return df

# --- FRONTEND ---
st.set_page_config(page_title="SENTINEL-NODE V5", layout="wide")

# Initialize Session State for Pagination
if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 0

col1, col2 = st.columns([3, 1])
with col1:
    st.title("📡 SENTINEL-NODE: Risk Command")
    st.markdown("*Real-time Open Source Intelligence (OSINT)*")
with col2:
    st.write("### ⏳ Time Filter")
    selected_time = st.selectbox("Select Window", list(TIME_FILTERS.keys()), index=2)

st.markdown("---")

c1, c2 = st.columns([1, 3])

with c1:
    st.header("Target Vector")
    selected_target = st.radio("Choose Choke Point", list(TARGETS.keys()))
    
    st.markdown("---")
    if st.button("Initialize Scan", type="primary", use_container_width=True):
        st.session_state['page_number'] = 0 # Reset to page 1 on new search
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
        
        # --- PAGINATION CONTROLS (Bottom Logic moved here for flow) ---
        total_items = len(df)
        
        # Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric("TOTAL INTEL FOUND", total_items)
        m2.metric("CRITICAL THREATS", len(df[df['Risk'] == "CRITICAL"]))
        m3.metric("SOURCE WINDOW", selected_time)
        
        st.markdown("### 🛑 Threat Feed (Sorted by Severity)")

        # Pagination Dropdown
        items_per_page = st.selectbox(
            "Articles per page:", 
            options=[5, 10, 25, 50, 100], 
            index=0
        )
        
        # Calculate Pages
        total_pages = max(1, (total_items // items_per_page) + (1 if total_items % items_per_page > 0 else 0))
        current_page = st.session_state['page_number']
        
        # Ensure we don't go out of bounds
        if current_page >= total_pages:
            current_page = total_pages - 1
            st.session_state['page_number'] = current_page

        # Slice Data
        start_idx = current_page * items_per_page
        end_idx = start_idx + items_per_page
        page_data = df.iloc[start_idx:end_idx]

        # Display Cards
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
                st.write(f"**AI Risk Score:** {row['Sentiment']} (Lower is worse)")
                st.markdown(f"[Read Article]({row['Link']})")

        st.markdown("---")
        
        # Navigation Buttons
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if st.button("⬅️ Previous"):
                if st.session_state['page_number'] > 0:
                    st.session_state['page_number'] -= 1
                    st.rerun()
        
        with col_info:
            st.markdown(f"<div style='text-align: center'>Page <b>{current_page + 1}</b> of <b>{total_pages}</b></div>", unsafe_allow_html=True)
        
        with col_next:
            if st.button("Next ➡️"):
                if st.session_state['page_number'] < total_pages - 1:
                    st.session_state['page_number'] += 1
                    st.rerun()

    else:
        st.info("👈 Select a target and click 'Initialize Scan' to begin.")

st.sidebar.caption("System: Sentinel-Node V5.0 | Status: Active")
