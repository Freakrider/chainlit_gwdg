import chainlit as cl
from openai import OpenAI
from config_manager import ConfigManager

base_url = "https://chat-ai.academiccloud.de/v1"
config_manager = ConfigManager(base_url)

@cl.on_chat_start
async def start():
    settings = await config_manager.load_settings()
    chat_settings = cl.ChatSettings(settings)
    await chat_settings.send()

@cl.on_settings_update
async def update_settings(settings):
    await config_manager.update_settings(settings)

@cl.on_message
async def main(message: cl.Message):
    api_key = config_manager.get_setting_value("GWDG_API_KEY")
    model = config_manager.get_setting_value("ACTIVEMODEL")
    temperature = config_manager.get_setting_value("Temperature")
    max_tokens = config_manager.get_setting_value("MaxTokens")

    if not api_key or not model:
        await cl.Message(content="Please set your API key and select a model in the settings.").send()
        return

    client = OpenAI(api_key=api_key, base_url=base_url)
    
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message.content}],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        content = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content += chunk.choices[0].delta.content
                await msg.stream_token(chunk.choices[0].delta.content)
        
        await msg.update()
    except Exception as e:
        await cl.Message(content=f"An error occurred: {str(e)}").send()

if __name__ == "__main__":
    cl.run()