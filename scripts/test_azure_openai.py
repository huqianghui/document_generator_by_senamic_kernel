import asyncio
import os
from dotenv import load_dotenv
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory

async def test_azure_openai():
    # Clear environment variables first
    for key in list(os.environ.keys()):
        if key.startswith('AZURE_OPENAI'):
            del os.environ[key]
    
    load_dotenv(override=True)
    
    print("Testing Azure OpenAI connection...")
    
    # Print configuration
    deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    
    print(f"Deployment name: {deployment_name}")
    print(f"Endpoint: {endpoint}")
    print(f"API Version: {api_version}")
    
    try:
        # Create Azure OpenAI service
        azure_openai = AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=api_version,
        )
        
        # Create a simple chat history
        chat_history = ChatHistory()
        chat_history.add_user_message("Hello, can you respond with a simple greeting?")
        
        # Test the connection
        response = await azure_openai.get_chat_message_content(
            chat_history=chat_history,
            settings=azure_openai.get_prompt_execution_settings_class()(
                max_tokens=100,
                temperature=0.0
            )
        )
        
        print(f"Success! Response: {response.content}")
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    asyncio.run(test_azure_openai())
