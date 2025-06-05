import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_weather_api():
    """Test OpenWeatherMap API key"""
    
    # Get API key from environment
    api_key = os.getenv('OPENWEATHER_API_KEY')
    
    print("🔍 Testing OpenWeatherMap API...")
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    
    if api_key:
        print(f"API Key length: {len(api_key)} characters")
        print(f"API Key starts with: {api_key[:8]}...")
    else:
        print("❌ No API key found in environment variables!")
        return False
    
    # Test API call
    test_city = "London"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={test_city}&appid={api_key}&units=metric"
    
    try:
        print(f"\n🌐 Testing API call for {test_city}...")
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful!")
            print(f"City: {data['name']}")
            print(f"Temperature: {data['main']['temp']}°C")
            print(f"Weather: {data['weather'][0]['description']}")
            return True
        else:
            error_data = response.json()
            print(f"❌ API Error: {error_data}")
            
            # Common error codes
            if response.status_code == 401:
                print("🔑 Error 401: Invalid API key")
                print("Solutions:")
                print("1. Check if your API key is correct")
                print("2. Make sure the API key is activated (can take up to 2 hours)")
                print("3. Verify you're using the correct API key from your OpenWeatherMap account")
            elif response.status_code == 429:
                print("⏰ Error 429: Too many requests")
                print("You've exceeded the API rate limit")
            
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_weather_api()