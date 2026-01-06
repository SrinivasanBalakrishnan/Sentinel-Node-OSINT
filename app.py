import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
import concurrent.futures  # ADDED: For parallel scanning
import time

# --- CONFIGURATION ---
REGIONS = {
    "🌎 Americas": {
        "Panama Canal": '"Panama Canal" OR "Gatun Lake" OR "Panama drought" OR "Maersk Panama"',
        "Gulf of Mexico": '"Gulf of Mexico oil" OR "Pemex platform" OR "US gulf coast port"',
        "Latin America Minerals": '"Lithium triangle" OR "Chile lithium" OR "Peru copper mines"'
    },
    "🌍 MENA": {
        "Red Sea / Suez": '"Red Sea" OR "Suez Canal" OR "Houthi" OR "Bab el-Mandeb"',
        "Strait of Hormuz": '"Strait of Hormuz" OR "Iranian navy" OR "oil tanker seized"',
        "Eastern Mediterranean": '"Eastern Mediterranean gas" OR "Cyprus Exclusive Economic Zone"'
    },
    "🌏 Indo-Pacific": {
        "Strait of Malacca": '"Strait of Malacca" OR "Singapore Strait" OR "Malacca Strait"',
        "Taiwan Strait": '"Taiwan Strait" OR "PLA navy" OR "TSMC" OR "Taiwan defense"',
        "South China Sea": '"South China Sea" OR "Spratly Islands" OR "Second Thomas Shoal"',
        "Indian Ocean": '"Indian Ocean" OR "Hambantota port" OR "Diego Garcia"'
    },
    "🌊 Oceania": {
        "Pacific Island Chains": '"Solomon Islands china" OR "Papua New Guinea port"',
        "Coral Sea": '"Coral Sea" OR "Great Barrier Reef shipping"'
    }
}

INDUSTRIES = {
    "📱 Semiconductors": '"TSMC" OR "Nvidia" OR "Foxconn" OR "ASML" OR "chip shortage"',
    "🔋 Critical Minerals": '"Lithium supply" OR "Cobalt mining" OR "Rare earth elements"',
    "⚡ Renewable Energy": '"Solar panel supply chain" OR "Wind turbine components"',
    "🛡️ Defense Ind. Base": '"Lockheed Martin supply" OR "Artillery shell production"',
    "🌾 Food Security": '"Wheat export ban" OR "Rice export india" OR "Fertilizer shortage"'
}

# REFINED KILL SWITCH: Specific phrases to avoid false positives on "drone" or "suspended"
CRITICAL_PHRASES = [
    "missile attack", "drone strike", "ship sinking", "vessel sinking",
    "port blocked", "canal blocked", "navigation suspended", 
    "sanctions imposed", "cargo seized", "oil spill", "collision at sea"
]

EXCLUDED_TERMS = ["Football", "Cricket", "Movie", "Celeb", "Gossip", "Reality TV"]

# --- HELPER FUNCTIONS ---
def parse_date(entry):
    """Safely extracts date from RSS entry, falling back to Now if missing."""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])
    return datetime.now()

def get_date_string(days_ago):
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

def fetch_url(url):
    """Simple wrapper for parallel execution."""
    return feedparser.parse(url)

def build_search_url(query, when=None, after=None, before=None):
    base_query = query.replace(" ", "%20")
    if after and before:
        # Google News RSS strict date slicing
        final_query = f"{base_query}+after:{after}+before:{before}"
    elif when:
        final_query = f"{base_query}%20when:{when}"
    else:
        final_query = base_query
    
    return f"https://news.google.com/rss/search?q={final_query}&hl=en-IN&gl=IN&ceid=IN:en"

def get_intel_concurrent(query_string, time_mode):
    """Fetches data using ThreadPool for 3x speedup on deep dives."""
    urls = []
    
    if time_mode in ["Last 24 Hours", "Last 7 Days"]:
        map_time = {"Last 24 Hours": "1d", "Last 7 Days": "7d"}
        urls.append(build_search_url(query_string, when=map_time[time_mode]))

    elif time_mode == "Past 1 Month":
        # Create 3 time slices to bypass Google's 100-item limit
        urls.append(build_search_url(query_string, when="7d")) # Week 1
        urls.append(build_search_url(query_string, after=get_date_string(14), before=get_date_string(7))) # Week 2
        urls.append(build_search_url(query_string, after=get_date_string(30), before=get_date_string(14))) # Weeks 3-4

    # PARALLEL EXECUTION
    all_feeds = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(fetch_url, urls)
        all_feeds = list(results)

    # PROCESS
    processed_data = []
    seen_links = set() # Dedup by Link is safer than Title

    for feed in all_feeds:
        for entry in feed.entries:
            # Noise Filter
            if any(term.lower() in entry.title.lower() for term in EXCLUDED_TERMS):
                continue
            
            # Deduplication (Link based)
            if entry.link in seen_links:
                continue
            seen_links.add(entry.link)

            pub_date = parse_date(entry)
            pub_date_str = pub_date.strftime("%Y-%m-%d")

            # AI Analysis
            text = f"{entry.title} {entry.get('summary', '')}"
            blob = TextBlob(text)
            sentiment = blob.sentiment.polarity
            
            # Risk Logic
            risk_score = "LOW"
            if sentiment < -0.05: risk_score = "MEDIUM"
            if sentiment < -0.2: risk_score = "HIGH"
            
            # Hard-Coded Critical Overrides
            title_lower = entry.title.lower()
            if any(phrase in title_lower for phrase in CRITICAL_PHRASES):
                risk_score = "CRITICAL"
            # Single keyword overrides (use sparingly)
            if "houthi" in title_lower and "attack" in title_lower:
                risk_score = "CRITICAL"

            processed_data.append({
                "Title": entry.title,
                "Link": entry.link,
                "Date": pub_date_str,
                "ObjDate": pub_date, # For sorting
                "Risk": risk_score,
                "Sentiment": round(sentiment, 2),
                "Source": entry.source.get('title', 'Google News')
            })

    df = pd.DataFrame(processed_data)
    if not df.empty:
        df = df.sort_values(by=['ObjDate'], ascending=False)
        
    return df

# --- FRONTEND ---
st.set_page_config(page_title="SENTINEL-NODE V13", layout="wide")

# STATE MANAGEMENT: Initialize 'active_scan' to persist data across re-runs
if 'active_scan' not in st.session_state:
    st.session_state['active_scan'] = {'target': None, 'query': None, 'data': None}
if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 0

# SIDEBAR
st.sidebar.title("🏭 Industry Monitor")
selected_industry = st.sidebar.selectbox("Select Sector", ["None"] + list(INDUSTRIES.keys()))

st.sidebar.markdown("---")
st.sidebar.write("### ⚙️ Scan Settings")
time_mode = st.sidebar.selectbox("Time Window", ["Last 24 Hours", "Last 7 Days", "Past 1 Month"], index=1)
threat_filter = st.sidebar.selectbox("Threat Level", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"], index=0)

# APP HEADER
st.title("📡 SENTINEL-NODE: Global Command")

# TABS LAYOUT
tab1, tab2, tab3, tab4 = st.tabs(list(REGIONS.keys()))

# LOGIC HANDLER: What triggered the scan?
trigger_target = None
trigger_query = None

# 1. Industry Trigger
if selected_industry != "None":
    st.info(f"🔭 **MODE:** Industry Scan - {selected_industry}")
    if st.button("🚀 INITIALIZE INDUSTRY SCAN", type="primary", use_container_width=True):
        trigger_target = selected_industry
        trigger_query = INDUSTRIES[selected_industry]

# 2. Map Trigger (Only show if no industry selected to avoid clutter)
else:
    def render_buttons(region_key, cols_count):
        cols = st.columns(cols_count)
        for i, (name, query) in enumerate(REGIONS[region_key].items()):
            if cols[i % cols_count].button(f"📍 {name}", use_container_width=True):
                return name, query
        return None, None

    with tab1:
        t, q = render_buttons("🌎 Americas", 3)
        if t: trigger_target, trigger_query = t, q
    with tab2:
        t, q = render_buttons("🌍 MENA", 3)
        if t: trigger_target, trigger_query = t, q
    with tab3:
        t, q = render_buttons("🌏 Indo-Pacific", 4)
        if t: trigger_target, trigger_query = t, q
    with tab4:
        t, q = render_buttons("🌊 Oceania", 2)
        if t: trigger_target, trigger_query = t, q

# EXECUTION: If a trigger happened, update Session State and Run
if trigger_target:
    st.session_state['page_number'] = 0
    with st.spinner(f"Scanning Vector: {trigger_target} ({time_mode})..."):
        df_result = get_intel_concurrent(trigger_query, time_mode)
        # Store in session state so it survives re-runs
        st.session_state['active_scan'] = {
            'target': trigger_target,
            'query': trigger_query,
            'data': df_result.to_dict('records') if not df_result.empty else []
        }

# RENDER RESULTS (Always read from Session State)
active_data = st.session_state['active_scan']['data']
active_target = st.session_state['active_scan']['target']

st.markdown("---")
if active_target and active_data is not None:
    df = pd.DataFrame(active_data)
    
    # Filter by Threat (Visual only, doesn't delete data)
    if threat_filter != "All":
        df = df[df['Risk'] == threat_filter]

    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("TARGET", active_target)
    m2.metric("INTEL FOUND", len(df))
    if not df.empty:
        m3.metric("CRITICAL THREATS", len(df[df['Risk'] == "CRITICAL"]))
    
    st.markdown("### 🛑 Live Feed")
    
    if df.empty:
        st.warning(f"No events found matching threat level: **{threat_filter}**")
    else:
        # Pagination Logic
        if 'items_per_page' not in st.session_state: st.session_state['items_per_page'] = 5
        
        total_pages = max(1, (len(df) // st.session_state['items_per_page']) + (1 if len(df) % st.session_state['items_per_page'] > 0 else 0))
        if st.session_state['page_number'] >= total_pages: st.session_state['page_number'] = 0
        
        start_idx = st.session_state['page_number'] * st.session_state['items_per_page']
        end_idx = start_idx + st.session_state['items_per_page']
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
                st.markdown(f"[Read Article]({row['Link']})")

        # Pagination Controls
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("⬅️ Previous"):
                if st.session_state['page_number'] > 0:
                    st.session_state['page_number'] -= 1
                    st.rerun()
        with c2:
            st.markdown(f"<div style='text-align: center'>Page {st.session_state['page_number'] + 1} of {total_pages}</div>", unsafe_allow_html=True)
        with c3:
            if st.button("Next ➡️"):
                if st.session_state['page_number'] < total_pages - 1:
                    st.session_state['page_number'] += 1
                    st.rerun()

elif active_target is None:
    st.info("Select a Region or Industry to initialize command.")
else:
    st.error("No intelligence found.")
