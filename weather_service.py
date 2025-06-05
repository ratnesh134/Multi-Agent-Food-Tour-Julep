import requests
from datetime import datetime
import streamlit as st

class WeatherService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
    
    def get_weather_data(self, city):
        """Fetch real weather data from OpenWeatherMap API"""
        try:
            # Current weather
            current_url = f"{self.base_url}/weather?q={city}&appid={self.api_key}&units=metric"
            current_response = requests.get(current_url)
            current_data = current_response.json()
            
            if current_response.status_code != 200:
                raise Exception(f"Weather API error: {current_data.get('message', 'Unknown error')}")
            
            # Forecast data (for rain prediction)
            forecast_url = f"{self.base_url}/forecast?q={city}&appid={self.api_key}&units=metric"
            forecast_response = requests.get(forecast_url)
            forecast_data = forecast_response.json()
            
            # Extract current weather info
            weather_info = {
                "city": current_data["name"],
                "country": current_data["sys"]["country"],
                "temperature": round(current_data["main"]["temp"]),
                "feels_like": round(current_data["main"]["feels_like"]),
                "humidity": current_data["main"]["humidity"],
                "description": current_data["weather"][0]["description"].title(),
                "main_weather": current_data["weather"][0]["main"],
                "wind_speed": current_data["wind"]["speed"],
                "visibility": current_data.get("visibility", 0) / 1000,
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sunrise": datetime.fromtimestamp(current_data["sys"]["sunrise"]).strftime("%H:%M"),
                "sunset": datetime.fromtimestamp(current_data["sys"]["sunset"]).strftime("%H:%M")
            }
            
            # Check for rain in next 12 hours
            rain_probability = 0
            will_rain = False
            rain_times = []
            
            if forecast_response.status_code == 200:
                for forecast in forecast_data["list"][:4]:  # Next 12 hours
                    if "rain" in forecast:
                        will_rain = True
                        rain_times.append(datetime.fromtimestamp(forecast["dt"]).strftime("%H:%M"))
                    
                    if "pop" in forecast:
                        rain_probability = max(rain_probability, forecast["pop"] * 100)
            
            weather_info.update({
                "will_rain": will_rain,
                "rain_probability": round(rain_probability),
                "rain_times": rain_times
            })
            
            return weather_info
            
        except Exception as e:
            st.error(f"❌ Error fetching weather for {city}: {str(e)}")
            return None
    
    def get_dining_recommendation(self, weather_data):
        """Generate dining recommendations based on weather"""
        if not weather_data:
            return "Mixed indoor/outdoor dining recommended"
        
        temp = weather_data['temperature']
        will_rain = weather_data['will_rain']
        rain_prob = weather_data['rain_probability']
        main_weather = weather_data['main_weather']
        
        if will_rain or rain_prob > 70:
            return "🏠 **Indoor Dining Recommended** - High chance of rain today"
        elif temp < 15:
            return "🔥 **Cozy Indoor Spaces** - Cool weather perfect for warm, comfortable restaurants"
        elif temp > 30:
            return "❄️ **Air-Conditioned Venues** - Hot weather calls for cool, comfortable indoor dining"
        elif main_weather == "Clear" and 15 <= temp <= 25:
            return "🌤️ **Perfect for Outdoor Dining** - Ideal weather for terraces and street food"
        else:
            return "🍽️ **Mixed Indoor/Outdoor** - Pleasant conditions for various dining options"
