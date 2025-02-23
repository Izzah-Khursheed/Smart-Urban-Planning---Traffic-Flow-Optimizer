import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
import json

# API Keys
GROQ_API_KEY = "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"
HERE_API_KEY = "Z-INy7MKiZwfH6mAchEr0QPFaYuuo5QKqGxSnHxcKTY"

# Initialize session states
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'location_input' not in st.session_state:
    st.session_state.location_input = ""

# Page configuration
st.set_page_config(
    page_title="TrafficWise Urban Planner",
    page_icon="🚦",
    layout="wide"
)

# Sidebar configuration
st.sidebar.title("🚦 TrafficWise Urban Planner")
st.sidebar.markdown("Your AI Assistant for Traffic & Urban Planning")

# Temperature slider
temperature = st.sidebar.slider(
    "AI Response Variation:",
    min_value=0.0,
    max_value=1.0,
    value=0.7,
    step=0.1,
    help="Higher values provide more varied suggestions, lower values offer more consistent advice"
)

def geocode_address(address):
    """Convert address to coordinates using HERE Geocoding API"""
    url = f"https://geocode.search.hereapi.com/v1/geocode"
    params = {
        'q': address,
        'apiKey': HERE_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data['items']:
            position = data['items'][0]['position']
            return position['lat'], position['lng']
        return None
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")
        return None

def get_traffic_data(lat, lon, radius=1000):
    """Fetch real-time traffic data from HERE API"""
    url = f"https://traffic.ls.hereapi.com/traffic/6.2/flow.json"
    params = {
        'apiKey': HERE_API_KEY,
        'prox': f"{lat},{lon},{radius}"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Traffic data error: {str(e)}")
        return None

def generate_traffic_map(center_lat=30.3753, center_lng=69.3451):
    """Generate map with traffic data"""
    m = folium.Map(location=[center_lat, center_lng], zoom_start=13)
    
    # Add traffic data if available
    traffic_data = get_traffic_data(center_lat, center_lng)
    if traffic_data and 'RWS' in traffic_data:
        for rw in traffic_data['RWS']:
            for flow_item in rw.get('RW', []):
                for fi in flow_item.get('FIS', []):
                    for location in fi.get('FI', []):
                        if 'CF' in location:
                            # Add traffic flow visualization
                            points = location['CF'][0]['CF']
                            coordinates = [[p['lat'], p['lon']] for p in points]
                            # Color based on jam factor (0-10)
                            jam_factor = location['CF'][0].get('JF', 0)
                            color = 'green' if jam_factor < 4 else 'yellow' if jam_factor < 7 else 'red'
                            
                            folium.PolyLine(
                                coordinates,
                                color=color,
                                weight=5,
                                opacity=0.8,
                                tooltip=f"Traffic Jam Factor: {jam_factor}"
                            ).add_to(m)
    
    return m

# Sidebar map section
st.sidebar.subheader("Live Traffic Map")
location_input = st.sidebar.text_input(
    "Enter location to view traffic:",
    key="location_input",
    placeholder="Enter an address or location"
)

if location_input:
    coordinates = geocode_address(location_input)
    if coordinates:
        lat, lng = coordinates
        with st.sidebar:
            folium_static(generate_traffic_map(lat, lng))
    else:
        st.sidebar.error("Location not found. Please try another address.")
else:
    with st.sidebar:
        folium_static(generate_traffic_map())

# Rest of the chat interface remains the same
st.title("🚦 TrafficWise Urban Planner")
st.markdown("""
### Your AI Assistant for:
- 🚗 Traffic Route Optimization
- 🌆 Urban Congestion Solutions
- 🚦 Traffic Flow Analysis
- 🛣 Infrastructure Planning
""")

def chat_with_traffic_planner(user_message, temperature):
    """Send a message to Groq API's model and return the response."""
    enhanced_prompt = f"""As a traffic and urban planning expert, help with the following question 
    about traffic routes, urban congestion, or city planning: {user_message}
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": enhanced_prompt}],
        "temperature": temperature
    }
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error: Unable to connect to the API - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

def clear_chat():
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    role = message["role"]
    content = message["content"]
    st.markdown(f"👤 You:** {content}" if role == "user" else f"🚦 TrafficWise:** {content}")
    st.markdown("---")

def submit_message():
    if st.session_state.user_input:
        user_message = st.session_state.user_input
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        with st.spinner('Analyzing traffic patterns...'):
            bot_response = chat_with_traffic_planner(user_message, temperature)
        st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
        st.session_state.user_input = ""

st.text_input(
    "Ask about traffic routes, urban planning, or congestion solutions...",
    key="user_input",
    on_change=submit_message,
    placeholder="Example: What are the best routes to reduce congestion during peak hours?"
)

if st.button("🗑 Clear Chat"):
    clear_chat()

st.sidebar.markdown("""
### 🚗 Traffic Guidelines:
1. 🕒 *Peak Hours*
   - Morning: 7-9 AM
   - Evening: 4-7 PM

2. 🚸 *Safety First*
   - Follow speed limits
   - Watch for pedestrians

3. 🌍 *Eco-Friendly Options*
   - Consider public transport
   - Use carpooling

4. 🚦 *Smart Route Planning*
   - Check traffic updates
   - Use alternative routes

5. 📱 *Stay Informed*
   - Monitor traffic alerts
   - Check weather conditions
""")
