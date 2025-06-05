from julep import Julep
import streamlit as st
from utils import clean_response_text

class AgentServices:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = None
        self.agents = {}
    
    def initialize_client(self):
        """Initialize Julep client"""
        try:
            self.client = Julep(api_key=self.api_key)
            return True
        except Exception as e:
            st.error(f"❌ Error initializing Julep client: {str(e)}")
            return False
    
    def create_agents(self):
        """Create all required agents"""
        try:
            with st.spinner("🤖 Setting up AI agents..."):
                agent_configs = {
                    "weather": {
                        "name": "Weather Oracle",
                        "about": "Expert meteorologist who analyzes real-time weather data and provides precise dining recommendations."
                    },
                    "culinary": {
                        "name": "Food Culture Guru",
                        "about": "Local food culture expert specializing in authentic, traditional dishes."
                    },
                    "restaurant": {
                        "name": "Restaurant Detective",
                        "about": "Restaurant researcher who finds authentic, highly-rated establishments."
                    },
                    "tour": {
                        "name": "Storytelling Tour Guide",
                        "about": "Creative storyteller who crafts engaging, narrative-driven food tours."
                    },
                    "coordinator": {
                        "name": "Experience Coordinator",
                        "about": "Master coordinator who creates comprehensive, actionable tour guides."
                    }
                }
                
                for key, config in agent_configs.items():
                    self.agents[key] = self.client.agents.create(
                        name=config["name"],
                        model="claude-3.5-sonnet",
                        about=config["about"]
                    )
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error creating agents: {str(e)}")
            return False
    
    def chat_with_agent(self, agent_key, message):
        """Enhanced chat function with better response extraction"""
        if agent_key not in self.agents:
            return f"Agent {agent_key} not available"
        
        agent = self.agents[agent_key]
        
        try:
            session = self.client.sessions.create(agent=agent.id)
            
            response = self.client.sessions.chat(
                session_id=session.id,
                messages=[{"role": "user", "content": message}]
            )
            
            # Enhanced response extraction
            content = None
            
            # Try different ways to extract content
            if hasattr(response, 'messages') and response.messages:
                last_message = response.messages[-1]
                if hasattr(last_message, 'content'):
                    if isinstance(last_message.content, list):
                        # Handle list of content items
                        for item in last_message.content:
                            if hasattr(item, 'text'):
                                content = item.text
                                break
                            elif isinstance(item, dict) and 'text' in item:
                                content = item['text']
                                break
                            elif isinstance(item, str):
                                content = item
                                break
                    else:
                        content = last_message.content
            
            # Fallback methods
            if not content:
                for attr in ['content', 'text', 'message', 'output']:
                    if hasattr(response, attr):
                        attr_value = getattr(response, attr)
                        if attr_value:
                            content = str(attr_value)
                            break
            
            # Final fallback
            if not content:
                content = str(response)
            
            # Clean and format the response
            return clean_response_text(content)
            
        except Exception as e:
            st.warning(f"⚠️ Chat error with {agent.name}: {e}")
            return f"Unable to get response from {agent.name}. Please try again."
        
