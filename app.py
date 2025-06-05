import streamlit as st
import os
from dotenv import load_dotenv
from weather_service import WeatherService
from julep_service import JulepService
from utils import (
    load_css, get_weather_emoji, format_time, 
    validate_api_key, create_download_content,
    show_progress_with_message, clear_progress
)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title=os.getenv("APP_TITLE", "Weather-Aware Foodie Tours"),
    page_icon=os.getenv("APP_ICON", "🍜"),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
load_css("styles.css")

# Initialize session state
if 'tours' not in st.session_state:
    st.session_state.tours = {}
if 'julep_service' not in st.session_state:
    st.session_state.julep_service = None
if 'weather_service' not in st.session_state:
    st.session_state.weather_service = None

def format_weather_display(weather_data):
    """Create beautiful weather display"""
    if not weather_data:
        return "Weather data unavailable"
    
    weather_emoji = get_weather_emoji(weather_data['description'])
    
    return f"""
    <div class="weather-card">
        <h2>{weather_emoji} {weather_data['city']}, {weather_data['country']}</h2>
        <h1>{weather_data['temperature']}°C</h1>
        <h3>{weather_data['description']}</h3>
        <div class="weather-stats">
            <div class="weather-stat">
                <strong>Feels Like:</strong><br>{weather_data['feels_like']}°C
            </div>
            <div class="weather-stat">
                <strong>Humidity:</strong><br>{weather_data['humidity']}%
            </div>
            <div class="weather-stat">
                <strong>Wind:</strong><br>{weather_data['wind_speed']} m/s
            </div>
            <div class="weather-stat">
                <strong>Rain Chance:</strong><br>{weather_data['rain_probability']}%
            </div>
        </div>
        <div style="margin-top: 1rem;">
            <span class="time-badge">🌅 Sunrise: {weather_data['sunrise']}</span>
            <span class="time-badge">🌇 Sunset: {weather_data['sunset']}</span>
        </div>
    </div>
    """

def initialize_services():
    """Initialize weather and Julep services"""
    # Get API keys from environment
    julep_key = os.getenv('JULEP_API_KEY')
    weather_key = os.getenv('OPENWEATHER_API_KEY')
    
    if not julep_key:
        st.error("❌ JULEP_API_KEY not found in environment variables!")
        st.info("Please add your Julep API key to the .env file")
        return False
    
    if not weather_key:
        st.error("❌ OPENWEATHER_API_KEY not found in environment variables!")
        st.info("Please add your OpenWeatherMap API key to the .env file")
        return False
    
    # Validate API keys
    julep_valid, julep_msg = validate_api_key(julep_key, "Julep API Key")
    weather_valid, weather_msg = validate_api_key(weather_key, "Weather API Key")
    
    if not julep_valid:
        st.error(f"❌ {julep_msg}")
        return False
    
    if not weather_valid:
        st.error(f"❌ {weather_msg}")
        return False
    
    # Initialize services
    try:
        # Weather service
        st.session_state.weather_service = WeatherService(weather_key)
        
        # Julep service
        julep_service = JulepService(julep_key)
        if julep_service.initialize_client() and julep_service.create_agents():
            st.session_state.julep_service = julep_service
            return True
        else:
            return False
            
    except Exception as e:
        st.error(f"❌ Error initializing services: {str(e)}")
        return False

def create_foodie_tour_for_city(city):
    """Create a complete foodie tour for a single city"""
    
    progress_bar, status_text = show_progress_with_message(0, "🌡️ Fetching real-time weather data...")
    
    # Get weather data
    weather_data = st.session_state.weather_service.get_weather_data(city)
    if not weather_data:
        clear_progress(progress_bar, status_text)
        st.error(f"❌ Could not fetch weather data for {city}")
        return None
    
    # Display weather card
    st.markdown(format_weather_display(weather_data), unsafe_allow_html=True)
    
    dining_rec = st.session_state.weather_service.get_dining_recommendation(weather_data)
    st.markdown(f'<div class="highlight-text">{dining_rec}</div>', unsafe_allow_html=True)
    
    # Step 1: Weather Analysis
    progress_bar.progress(25)
    status_text.text("🌤️ Analyzing weather for dining recommendations...")
    
    weather_prompt = f"""
    Analyze the current weather in {city} and provide specific dining recommendations:
    
    Current Conditions:
    - Temperature: {weather_data['temperature']}°C (feels like {weather_data['feels_like']}°C)
    - Weather: {weather_data['description']}
    - Rain Probability: {weather_data['rain_probability']}%
    - Humidity: {weather_data['humidity']}%
    - Wind Speed: {weather_data['wind_speed']} m/s
    
    Please provide:
    1. Specific dining recommendations based on these conditions
    2. Best times for outdoor dining (if applicable)
    3. Weather-appropriate food and drink suggestions
    4. Any special considerations for today's weather
    
    Keep your response conversational and practical.
    """
    
    weather_analysis = st.session_state.julep_service.chat_with_agent("weather", weather_prompt)
    
    # Step 2: Weather-appropriate dishes
    progress_bar.progress(50)
    status_text.text("🍜 Finding weather-appropriate local dishes...")
    
    dishes_prompt = f"""
    Recommend 3 iconic dishes from {city} that are perfect for today's weather:
    - Temperature: {weather_data['temperature']}°C
    - Conditions: {weather_data['description']}
    - Rain probability: {weather_data['rain_probability']}%
    
    For each dish, explain:
    1. What makes it iconic to {city}
    2. Why it's perfect for today's weather
    3. Its cultural significance
    
    Present this in a clear, engaging format.
    """
    
    dishes = st.session_state.julep_service.chat_with_agent("culinary", dishes_prompt)
    
    # Step 3: Find suitable restaurants
    progress_bar.progress(75)
    status_text.text("🏨 Finding weather-suitable restaurants...")
    
    restaurant_prompt = f"""
    Find the best restaurants in {city} for today's weather conditions:
    - Weather: {weather_data['temperature']}°C, {weather_data['description']}
    - Rain probability: {weather_data['rain_probability']}%
    - Recommended dining style: {dining_rec}
    
    For each restaurant, provide:
    1. Name and location
    2. Specialty dish
    3. Why it's perfect for today's weather (indoor/outdoor seating)
    4. What makes it special
    
    Focus on authentic, highly-rated places that suit today's conditions.
    """
    
    restaurants = st.session_state.julep_service.chat_with_agent("restaurant", restaurant_prompt)
    
    # Step 4: Create tour narrative
    progress_bar.progress(90)
    status_text.text("📖 Creating your personalized tour...")
    
    tour_prompt = f"""
    Create an engaging one-day foodie tour for {city} that adapts to today's weather:
    
    Weather Context: {weather_data['temperature']}°C, {weather_data['description']}, {weather_data['rain_probability']}% rain chance
    
    Include:
    1. Morning, afternoon, and evening activities
    2. Specific timing recommendations
    3. Weather-appropriate transitions between locations
    4. Cultural stories and local insights
    5. Backup plans if weather changes
    
    Make it feel like a personal guide is talking to the reader.
    """
    
    narrative = st.session_state.julep_service.chat_with_agent("tour", tour_prompt)
    
    # Step 5: Final coordination
    progress_bar.progress(100)
    status_text.text("🎯 Finalizing your complete guide...")
    
    coordinator_prompt = f"""
    Create a comprehensive, easy-to-follow foodie tour guide for {city} that incorporates:
    - Current weather conditions and recommendations
    - Weather-appropriate local dishes
    - Suitable restaurants for today's conditions
    - A complete day itinerary
    
    Format this as a practical guide that someone could actually use today, with clear sections and actionable advice.
    """
    
    final_tour = st.session_state.julep_service.chat_with_agent("coordinator", coordinator_prompt)
    
    clear_progress(progress_bar, status_text)
    st.success("✅ Tour complete!")
    
    return {
        "city": city,
        "weather_data": weather_data,
        "dining_recommendations": dining_rec,
        "weather_analysis": weather_analysis,
        "dishes": dishes,
        "restaurants": restaurants,
        "narrative": narrative,
        "final_tour": final_tour
    }

def display_tour(tour):
    """Display a single tour with beautiful formatting"""
    
    # Weather analysis section
    st.markdown('<div class="content-section fade-in">', unsafe_allow_html=True)
    st.markdown("### 🌤️ Weather Analysis & Dining Strategy")
    st.markdown(tour["weather_analysis"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Dishes section
    st.markdown('<div class="dish-card fade-in">', unsafe_allow_html=True)
    st.markdown("### 🍜 Perfect Dishes for Today's Weather")
    st.markdown(tour["dishes"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Restaurants section
    st.markdown('<div class="restaurant-card fade-in">', unsafe_allow_html=True)
    st.markdown("### 🏨 Weather-Perfect Restaurant Recommendations")
    st.markdown(tour["restaurants"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tour narrative
    st.markdown('<div class="tour-timeline fade-in">', unsafe_allow_html=True)
    st.markdown("### 📖 Your Weather-Adaptive Day Adventure")
    st.markdown(tour["narrative"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Final comprehensive guide
    st.markdown('<div class="content-section fade-in">', unsafe_allow_html=True)
    st.markdown("### 🎯 Complete Tour Guide")
    st.markdown(tour["final_tour"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Download button
    tour_content = create_download_content(tour)
    
    st.download_button(
        label="📥 Download Beautiful Tour Guide",
        data=tour_content,
        file_name=f"{tour['city']}_beautiful_foodie_tour.md",
        mime="text/markdown"
    )

def main():
    """Main application function"""
    
    # Header
    st.markdown('<h1 class="main-header">🍜 Weather-Aware Foodie Tours</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Discover authentic local cuisine tailored to real-time weather conditions!</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-header"><h3>⚙️ Configuration</h3></div>', unsafe_allow_html=True)
        
        # API Status
        julep_key = os.getenv('JULEP_API_KEY')
        weather_key = os.getenv('OPENWEATHER_API_KEY')
        
        if julep_key and weather_key:
            st.markdown('<div class="success-message">✅ API keys loaded from .env file</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-message">❌ API keys missing from .env file</div>', unsafe_allow_html=True)
            st.info("Please create a .env file with your API keys")
        
        st.markdown("---")
        
        # City selection
        st.markdown('<div class="sidebar-header"><h4>🌍 Select Cities</h4></div>', unsafe_allow_html=True)
        
        popular_cities = [
            "Tokyo", "Paris", "New York", "Bangkok", "Istanbul",
            "Rome", "Barcelona", "London", "Mumbai", "Seoul",
            "Mexico City", "Buenos Aires", "Cairo", "Sydney", "Berlin"
        ]
        
        selected_cities = st.multiselect(
            "Choose cities:",
            popular_cities,
            default=["Tokyo"],
            help="Select cities for weather-aware tours"
        )
        
        custom_city = st.text_input("Add custom city:")
        if custom_city and custom_city not in selected_cities:
            selected_cities.append(custom_city)
        
        st.markdown("---")
        
        # App info
        st.markdown('<div class="sidebar-header"><h4>ℹ️ About</h4></div>', unsafe_allow_html=True)
        st.info(f"Generated on: {format_time()}")
        
        if os.getenv("DEBUG") == "True":
            st.warning("🔧 Debug mode enabled")
    
    # Main content
    if not selected_cities:
        st.info("👈 Please select cities from the sidebar to start creating your weather-aware foodie tours!")
        return
    
    # Initialize services
    if st.session_state.julep_service is None or st.session_state.weather_service is None:
        if not initialize_services():
            return
        st.success("✅ Services initialized successfully!")
    
    # Generate tours button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Generate Beautiful Weather-Aware Tours", key="generate_tours"):
            st.session_state.tours = {}
            
            for city in selected_cities:
                st.markdown(f'<div class="city-card slide-in"><h3>🌆 Creating tour for {city}...</h3></div>', unsafe_allow_html=True)
                
                try:
                    tour = create_foodie_tour_for_city(city)
                    if tour:
                        st.session_state.tours[city] = tour
                        st.markdown(f'<div class="success-message">✅ {city} tour completed!</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                        st.markdown(f'<div class="error-message">❌ Error creating tour for {city}: {str(e)}</div>', unsafe_allow_html=True)
    
    # Display tours
    if st.session_state.tours:
        st.markdown("## 🗺️ Your Beautiful Weather-Aware Foodie Tours")
        
        if len(st.session_state.tours) > 1:
            tabs = st.tabs(list(st.session_state.tours.keys()))
            for i, (city, tour) in enumerate(st.session_state.tours.items()):
                with tabs[i]:
                    display_tour(tour)
        else:
            city, tour = next(iter(st.session_state.tours.items()))
            display_tour(tour)

if __name__ == "__main__":
    main()