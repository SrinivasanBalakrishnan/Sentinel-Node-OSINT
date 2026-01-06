import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
import concurrent.futures
import folium
from streamlit_folium import st_folium

# --- CONFIGURATION: GEOSPATIAL DATABASE ---
# We now add Coordinates (Lat, Lon) to every target for the map
GEO_TARGETS = {
    "Panama Canal": {"coords": [9.101, -79.695], "query": '"Panama Canal" OR "Gatun Lake" OR "Panama drought"', "region": "Americas"},
    "Gulf of Mexico": {"coords": [25.000, -90.000], "query": '"Gulf of Mexico oil" OR "Pemex platform"', "region": "Americas"},
    "Red Sea / Suez": {"coords": [20.000, 38.000], "query": '"Red Sea" OR "Suez Canal" OR "Houthi"', "region": "MENA"},
    "Strait of Hormuz": {"coords": [26.566, 56.416], "query": '"Strait of Hormuz" OR "Iranian navy" OR "tanker seized"', "region": "MENA"},
    "Strait of Malacca": {"coords": [4.000, 100.000], "query": '"Strait of Malacca" OR "Singapore Strait"', "region": "Indo-Pacific"},
    "Taiwan Strait": {"coords": [24.000, 119.000], "query": '"Taiwan Strait" OR "PLA navy" OR "TSMC"', "region": "Indo-Pacific"},
    "South China Sea": {"coords": [12.000, 113.000], "query": '"South China Sea" OR "Spratly Islands"', "region": "Indo-Pacific"},
    "Solomon Islands": {"coords": [-9.645, 160.156], "query": '"Solomon Islands china" OR "Pacific security"', "region": "Oceania"}
}

INDUSTRIES = {
    "📱 Semiconductors": '"TSMC" OR "Nvidia" OR "Foxconn" OR "ASML" OR "chip shortage"',
    "🔋 Critical Minerals": '"Lithium supply" OR "Cobalt mining" OR "Rare earth elements"',
    "⚡ Renewable Energy": '"Solar panel supply chain" OR "Wind turbine components"',
    "🛡️ Defense Ind. Base": '"Lockheed Martin supply" OR "Artillery shell production"',
    "🌾 Food Security": '"Wheat export ban" OR "Rice export india" OR "Fertilizer shortage"'
}

CRITICAL_PHRASES = ["missile attack", "drone strike", "ship sinking", "port blocked", "canal blocked", "sanctions imposed", "cargo seized", "collision at sea"]
EXCLUDED_TERMS = ["Football", "Cricket", "Movie", "Celeb", "Gossip"]

# --- HELPER FUNCTIONS ---
def parse_date(entry):
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    return datetime.now()

def get_date_string(days_ago):
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

def fetch_url(url):
    return feedparser.parse(url)

def build_search_url(query, when=None, after=None, before=None):
    base_query = query.replace(" ", "%20")
    if after and before:
        final_query = f"{base_query}+after:{after}+before:{before}"
    elif when:
        final_query = f"{base_query}%20when:{when}"
    else:
        final_query = base_query
    return f"https://news.google.com/rss/search?q={final_query}&hl=en-IN&gl=IN&ceid=IN:en"

def get_intel_concurrent(query_string, time_mode):
    urls = []
    if time_mode in ["Last 24 Hours", "Last 7 Days"]:
        map_time = {"Last 24 Hours": "1d", "Last 7 Days": "7d"}
        urls.append(build_search_url(query_string, when=map_time[time_mode]))
    elif time_mode == "Past 1 Month":
        urls.append(build_search_url(query_string, when="7d"))
        urls.append(build_search_url(query_string, after=get_date_string(14), before=get_date_string(7)))
        urls.append(build_search_url(query_string, after=get_date_string(30), before=get_date_string(14)))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(fetch_url, urls)
        all_feeds = list(results)

    processed_data = []
    seen_links = set()

    for feed in all_feeds:
        for entry in feed.entries:
            if any(term.lower() in entry.title.lower() for term in EXCLUDED_TERMS): continue
            if entry.link in seen_links: continue
            seen_links.add(entry.link)

            pub_date = parse_date(entry)
            text = f"{entry.title} {entry.get('summary', '')}"
            blob = TextBlob(text)
            sentiment = blob.sentiment.polarity
            
            risk_score = "LOW"
            if sentiment < -0.05: risk_score = "MEDIUM"
            if sentiment < -0.2: risk_score = "HIGH"
            if any(phrase in entry.title.lower() for phrase in CRITICAL_PHRASES): risk_score = "CRITICAL"

            processed_data.append({
                "Title": entry.title,
                "Link": entry.link,
                "Date": pub_date.strftime("%Y-%m-%d"),
                "Risk": risk_score,
                "Sentiment": round(sentiment, 2),
                "Source": entry.source.get('title', 'Google News')
            })

    df = pd.DataFrame(processed_data)
    if not df.empty:
        df = df.sort_values(by=['Date'], ascending=False)
    return df

# --- FRONTEND UI ---
st.set_page_config(page_title="SENTINEL-NODE V14", layout="wide")

if 'active_scan' not in st.session_state:
    st.session_state['active_scan'] = {'target': None, 'data': None}

st.sidebar.title("🏭 Global Industry")
selected_industry = st.sidebar.selectbox("Sector Monitor", ["None"] + list(INDUSTRIES.keys()))
st.sidebar.markdown("---")
time_mode = st.sidebar.selectbox("Time Window", ["Last 24 Hours", "Last 7 Days", "Past 1 Month"], index=1)
threat_filter = st.sidebar.selectbox("Threat Level", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"], index=0)

st.title("📡 SENTINEL-NODE: Enterprise Command")

# --- MAP LOGIC ---
# Create the base map
m = folium.Map(location=[20.0, 0.0], zoom_start=2)

# Add markers for each target
for name, data in GEO_TARGETS.items():
    # Color code regions for visual clarity
    color = "red" if data["region"] == "Indo-Pacific" else "blue" if data["region"] == "Americas" else "orange"
    
    folium.Marker(
        location=data["coords"],
        popup=name,
        tooltip=f"<b>{name}</b><br>Click to Scan",
        icon=folium.Icon(color=color, icon="info-sign")
    ).add_to(m)

# --- LAYOUT: MAP ON TOP, RESULTS BELOW ---
col_map, col_info = st.columns([3, 1])

with col_map:
    st.markdown("### 🗺️ Live Situation Map")
    # This renders the map and captures clicks
    map_data = st_folium(m, height=400, width=800)

with col_info:
    st.markdown("### 📋 Quick Stats")
    st.metric("Monitored Choke Points", len(GEO_TARGETS))
    st.metric("Global Industries", len(INDUSTRIES))
    st.info("👈 Click a marker on the map to initialize a regional scan.")

# --- INTERACTION LOGIC ---
trigger_target = None
trigger_query = None

# 1. Check for Map Clicks
if map_data and map_data.get("last_object_clicked"):
    # Find which target matches the clicked coordinates
    clicked_lat = map_data["last_object_clicked"]["lat"]
    clicked_lng = map_data["last_object_clicked"]["lng"]
    
    # Simple proximity match (Folium returns precise floats)
    for name, data in GEO_TARGETS.items():
        # Check if click is close to target (within small margin)
        if abs(data["coords"][0] - clicked_lat) < 0.1 and abs(data["coords"][1] - clicked_lng) < 0.1:
            trigger_target = name
            trigger_query = data["query"]

# 2. Check for Industry Selection (Overrides Map)
if selected_industry != "None":
    if st.sidebar.button("🚀 SCAN INDUSTRY"):
        trigger_target = selected_industry
        trigger_query = INDUSTRIES[selected_industry]

# 3. Execution
if trigger_target:
    with st.spinner(f"📡 Intercepting signals for: {trigger_target}..."):
        df_result = get_intel_concurrent(trigger_query, time_mode)
        st.session_state['active_scan'] = {
            'target': trigger_target,
            'data': df_result.to_dict('records')
        }

# --- RESULTS DASHBOARD ---
active_data = st.session_state['active_scan']['data']
active_target = st.session_state['active_scan']['target']

if active_target and active_data is not None:
    st.markdown("---")
    st.markdown(f"### 🛑 Intelligence Feed: {active_target}")
    
    df = pd.DataFrame(active_data)
    if threat_filter != "All":
        df = df[df['Risk'] == threat_filter]

    if df.empty:
        st.warning("No threats detected matching criteria.")
    else:
        # Mini-Dashboard Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("ARTICLES ANALYZED", len(active_data)) # Total before filter
        m2.metric("DISPLAYED ALERTS", len(df)) # Total after filter
        m3.metric("CRITICAL EVENTS", len(df[df['Risk'] == "CRITICAL"]))

        for _, row in df.iterrows():
            if row['Risk'] == "CRITICAL":
                st.error(f"🔴 **CRITICAL:** {row['Title']}")
            elif row['Risk'] == "HIGH":
                st.warning(f"🟠 **HIGH:** {row['Title']}")
            elif row['Risk'] == "MEDIUM":
                st.warning(f"🟡 **MEDIUM:** {row['Title']}")
            else:
                st.success(f"🟢 **STABLE:** {row['Title']}")
            
            with st.expander(f"See details ({row['Date']})"):
                st.write(f"**Source:** {row['Source']}")
                st.markdown(f"[>> Read Full Intelligence Report]({row['Link']})")
