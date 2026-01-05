import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
import time

# --- CONFIGURATION: GLOBAL TARGET VECTOR DATABASE ---
# We organize targets by REGION and by INDUSTRY

REGIONS = {
    "🌎 Americas": {
        "Panama Canal": '"Panama Canal" OR "Gatun Lake" OR "Panama drought" OR "Maersk Panama"',
        "Gulf of Mexico": '"Gulf of Mexico oil" OR "Pemex platform" OR "US gulf coast port"',
        "Latin America Minerals": '"Lithium triangle" OR "Chile lithium" OR "Peru copper mines"'
    },
    "🌍 MENA (Middle East & North Africa)": {
        "Red Sea / Suez": '"Red Sea" OR "Suez Canal" OR "Houthi" OR "Bab el-Mandeb"',
        "Strait of Hormuz": '"Strait of Hormuz" OR "Iranian navy" OR "oil tanker seized"',
        "Eastern Mediterranean": '"Eastern Mediterranean gas" OR "Cyprus Exclusive Economic Zone" OR "Libya port"'
    },
    "🌏 Indo-Pacific": {
        "Strait of Malacca": '"Strait of Malacca" OR "Singapore Strait" OR "Malacca Strait"',
        "Taiwan Strait": '"Taiwan Strait" OR "PLA navy" OR "TSMC" OR "Taiwan defense"',
        "South China Sea": '"South China Sea" OR "Spratly Islands" OR "Second Thomas Shoal"',
        "Indian Ocean": '"Indian Ocean" OR "Hambantota port" OR "Diego Garcia" OR "Andaman Sea"'
    },
    "🌊 Oceania": {
        "Pacific Island Chains": '"Solomon Islands china" OR "Papua New Guinea port" OR "Vanuatu security"',
        "Coral Sea": '"Coral Sea" OR "Great Barrier Reef shipping" OR "Australia navy"'
    }
}

INDUSTRIES = {
    "📱 Semiconductors": '"TSMC" OR "Nvidia" OR "Foxconn" OR "ASML" OR "chip shortage" OR "semiconductor supply chain"',
    "🔋 Critical Minerals": '"Lithium supply" OR "Cobalt mining" OR "Rare earth elements" OR "Graphite china export"',
    "⚡ Renewable Energy": '"Solar panel supply chain" OR "Wind turbine components" OR "Green hydrogen transport"',
    "🛡️ Defense Industrial Base": '"Lockheed Martin supply" OR "Artillery shell production" OR "Drone components shortage"',
    "🌾 Food Security": '"Wheat export ban" OR "Rice export india" OR "Fertilizer shortage" OR "Global grain supply"'
}

EXCLUDED_TERMS = [
    "Football", "Cricket", "Movie", "Celeb", "Gossip", "Reality TV",
    # We keep Ukraine/Russia/Gaza active for Global Scan, but you can uncomment below to hide them
    # "Ukraine", "Russia", "Gaza", "Hamas" 
]

# --- HELPER FUNCTIONS ---
def parse_date(date_str):
    try:
        struct_time = feedparser._parse_date(date_str)
        return datetime(*struct_time[:6])
    except:
        return datetime.now()

def get_date_string(days_ago):
    d = datetime.now() - timedelta(days=days_ago)
    return d.strftime("%Y-%m-%d")

def fetch_rss_url(query, after_date=None, before_date=None, when_param=None):
    base_query = query.replace(" ", "%20")
    if after_date and before_date:
        final_query = f"{base_query}+after:{after_date}+before:{before_date}"
    elif when_param:
        final_query = f"{base_query}%20when:{when_param}"
    else:
        final_query = base_query
    return f"https://news.google.com/rss/search?q={final_query}&hl=en-IN&gl=IN&ceid=IN:en"

def get_intel_deep_dive(query_string, time_mode):
    all_feeds = []
    
    # STRATEGY: Time Slicing
    if time_mode in ["Last 24 Hours", "Last 7 Days"]:
        map_time = {"Last 24 Hours": "1d", "Last 7 Days": "7d"}
        url = fetch_rss_url(query_string, when_param=map_time[time_mode])
        all_feeds.append(feedparser.parse(url))

    elif time_mode == "Past 1 Month":
        url1 = fetch_rss_url(query_string, when_param="7d")
        url2 = fetch_rss_url(query_string, after_date=get_date_string(14), before_date=get_date_string(7))
        url3 = fetch_rss_url(query_string, after_date=get_date_string(30), before_date=get_date_string(14))
        all_feeds = [feedparser.parse(url1), feedparser.parse(url2), feedparser.parse(url3)]

    # PROCESS
    processed_data = []
    seen_titles = set()

    for feed in all_feeds:
        for entry in feed.entries:
            if any(term.lower() in entry.title.lower() for term in EXCLUDED_TERMS):
                continue
            
            if entry.title.lower() in seen_titles:
                continue
            seen_titles.add(entry.title.lower())

            pub_date_obj = parse_date(entry.published)
            pub_date_str = pub_date_obj.strftime("%Y-%m-%d")

            text_to_analyze = f"{entry.title} {entry.get('summary', '')}"
            blob = TextBlob(text_to_analyze)
            sentiment = blob.sentiment.polarity
            
            risk_score = "LOW"
            if sentiment < -0.05: risk_score = "MEDIUM"
            if sentiment < -0.2: risk_score = "HIGH"
            
            critical_words = ["attack", "missile", "sinking", "blocked", "collision", "suspended", "ban", "sanction", "drone", "seized"]
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
        df = df.sort_values(by=['Date'], ascending=False)
        
    return df

# --- FRONTEND UI ---
st.set_page_config(page_title="SENTINEL-NODE V12", layout="wide")

if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 0

# --- SIDEBAR (INDUSTRY FILTER) ---
st.sidebar.title("🏭 Industry Monitor")
st.sidebar.markdown("Select a Global Critical Industry to bypass regional maps.")

selected_industry = st.sidebar.selectbox("Select Sector", ["None"] + list(INDUSTRIES.keys()))
st.sidebar.markdown("---")
st.sidebar.write("### ⚙️ Scan Settings")
time_mode = st.sidebar.selectbox("Time Window", ["Last 24 Hours", "Last 7 Days", "Past 1 Month"], index=1)
threat_filter = st.sidebar.selectbox("Threat Level", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"], index=0)

# --- MAIN MAP UI ---
st.title("📡 SENTINEL-NODE: Global Command")
st.markdown("### 🗺️ Theater of Operations")
st.markdown("Select a Region to view active choke points, or use the Sidebar for Industry scanning.")

# REGIONAL TABS (The "Map")
tab1, tab2, tab3, tab4 = st.tabs(list(REGIONS.keys()))

selected_vector = None
final_query = None

# LOGIC: Check if Industry is selected first
if selected_industry != "None":
    st.info(f"🔭 **MODE:** Industry Scan - {selected_industry}")
    if st.button("🚀 INITIALIZE INDUSTRY SCAN", type="primary", use_container_width=True):
        selected_vector = selected_industry
        final_query = INDUSTRIES[selected_industry]

else:
    # REGION 1: AMERICAS
    with tab1:
        st.write("#### 🌎 North & South America Choke Points")
        cols = st.columns(3)
        for i, (name, query) in enumerate(REGIONS["🌎 Americas"].items()):
            if cols[i % 3].button(f"📍 {name}", use_container_width=True):
                selected_vector = name
                final_query = query

    # REGION 2: MENA
    with tab2:
        st.write("#### 🌍 Middle East & North Africa Choke Points")
        cols = st.columns(3)
        for i, (name, query) in enumerate(REGIONS["🌍 MENA (Middle East & North Africa)"].items()):
            if cols[i % 3].button(f"📍 {name}", use_container_width=True):
                selected_vector = name
                final_query = query

    # REGION 3: INDO-PACIFIC
    with tab3:
        st.write("#### 🌏 Indo-Pacific Choke Points")
        cols = st.columns(4)
        for i, (name, query) in enumerate(REGIONS["🌏 Indo-Pacific"].items()):
            if cols[i % 4].button(f"📍 {name}", use_container_width=True):
                selected_vector = name
                final_query = query

    # REGION 4: OCEANIA
    with tab4:
        st.write("#### 🌊 Oceania & Pacific Islands")
        cols = st.columns(2)
        for i, (name, query) in enumerate(REGIONS["🌊 Oceania"].items()):
            if cols[i % 2].button(f"📍 {name}", use_container_width=True):
                selected_vector = name
                final_query = query

# --- EXECUTION ENGINE ---
if selected_vector and final_query:
    st.session_state['page_number'] = 0
    with st.spinner(f"Scanning Vector: {selected_vector}..."):
        df_result = get_intel_deep_dive(final_query, time_mode)
        st.session_state['data'] = df_result.to_dict('records') if not df_result.empty else None
        st.session_state['target'] = selected_vector

# --- RESULTS DISPLAY ---
st.markdown("---")
if 'data' in st.session_state and st.session_state['data'] is not None:
    df = pd.DataFrame(st.session_state['data'])
    
    if threat_filter != "All":
        df = df[df['Risk'] == threat_filter]
    
    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("TARGET", st.session_state['target'])
    m2.metric("INTEL FOUND", len(df))
    if not df.empty:
        m3.metric("CRITICAL THREATS", len(df[df['Risk'] == "CRITICAL"]))
    
    st.markdown(f"### 🛑 Live Feed")
    
    if df.empty:
        st.warning(f"No events found matching threat level: **{threat_filter}**")
    else:
        # Pagination
        if 'items_per_page' not in st.session_state: st.session_state['items_per_page'] = 5
        items_per_page = st.session_state['items_per_page']
        total_pages = max(1, (len(df) // items_per_page) + (1 if len(df) % items_per_page > 0 else 0))
        
        if st.session_state['page_number'] >= total_pages: st.session_state['page_number'] = 0
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

        # Controls
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("⬅️ Previous"):
                if current_page > 0:
                    st.session_state['page_number'] -= 1
                    st.rerun()
        with c2:
            st.markdown(f"<div style='text-align: center'>Page {current_page + 1} of {total_pages}</div>", unsafe_allow_html=True)
        with c3:
            if st.button("Next ➡️"):
                if current_page < total_pages - 1:
                    st.session_state['page_number'] += 1
                    st.rerun()

elif 'data' in st.session_state and st.session_state['data'] is None:
    st.error("No intelligence found for this sector.")
