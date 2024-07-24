import os
from dotenv import load_dotenv, set_key
import chainlit as cl
from chainlit.input_widget import InputWidget, TextInput, Slider, Select
import requests
import json
from typing import List, Dict, Any

class ConfigManager:
    def __init__(self, base_url: str):
        load_dotenv()
        self.base_url = base_url
        self.settings: List[InputWidget] = []
        self.env_path = os.path.join(os.path.dirname(__file__), ".env")

    @staticmethod
    def update_env_file(env_path: str, key: str, value: Any):
        if value is not None:
            set_key(env_path, key, str(value))

    @staticmethod
    def get_env_value(key: str) -> str:
        return os.getenv(key, "")

    async def load_settings(self) -> List[InputWidget]:
        current_settings = cl.user_session.get("settings", {})
        self.settings = []

        # Add API Key setting
        api_key = current_settings.get("GWDG_API_KEY", self.get_env_value("GWDG_API_KEY"))
        self.settings.append(TextInput(
            id="GWDG_API_KEY",
            label="GWDG API Key",
            initial=api_key,
            placeholder="Enter your GWDG API Key here"
        ))

        # Add Temperature setting
        temperature = current_settings.get("Temperature", 0.7)
        self.settings.append(Slider(
            id="Temperature",
            label="Temperature",
            initial=temperature,
            min=0,
            max=2,
            step=0.1
        ))

        # Add MaxTokens setting
        max_tokens = current_settings.get("MaxTokens", 4000)
        self.settings.append(Slider(
            id="MaxTokens",
            label="Max Tokens",
            initial=max_tokens,
            min=50,
            max=4000,
            step=50
        ))

        # Load models if API Key is available
        if api_key:
            models = await self.get_available_models(api_key)
            if models:
                current_model = current_settings.get("ACTIVEMODEL")
                initial_index = models.index(current_model) if current_model in models else 0
                self.settings.append(Select(
                    id="ACTIVEMODEL",
                    label="GWDG - Model",
                    values=models,
                    initial_index=initial_index
                ))

        return self.settings

    async def get_available_models(self, api_key: str) -> List[str]:
        try:
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                models = json.loads(response.text)
                return [model["id"] for model in models]
            else:
                await cl.Message(content=f"API Error: {response.status_code} - {response.text}").send()
                return []
        except Exception as e:
            await cl.Message(content=f"Exception occurred: {str(e)}").send()
            return []

    async def update_settings(self, new_settings: Dict[str, Any]):
        current_settings = cl.user_session.get("settings", {})
        current_settings.update(new_settings)
        cl.user_session.set("settings", current_settings)

        # Update env file
        for key, value in new_settings.items():
            self.update_env_file(self.env_path, key.upper(), value)

        # Reload environment variables
        load_dotenv(self.env_path, override=True)

        # Reload settings
        await self.load_settings()

        # Update chat settings
        chat_settings = cl.ChatSettings(self.settings)
        await chat_settings.send()

    def get_setting_value(self, key: str) -> Any:
        # First, try to get the value from the environment
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value
        
        # If not found in environment, get from session settings
        current_settings = cl.user_session.get("settings", {})
        return current_settings.get(key)