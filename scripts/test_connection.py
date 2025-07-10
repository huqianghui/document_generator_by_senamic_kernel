#!/usr/bin/env python3

import asyncio
import os
from dotenv import load_dotenv
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory

async def test_azure_openai_connection():
    """Test the Azure OpenAI connection with current configuration."""
    
    load_dotenv()
    
    # Print current configuration
    print("Current configuration:")
    print(f"Deployment: {os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT_NAME')}")
    print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    print(f"API Version: {os.getenv('AZURE_OPENAI_API_VERSION')}")
    print(f"API Key: {'*' * 20}...{os.getenv('AZURE_OPENAI_API_KEY', '')[-4:]}")
    print()
    
    try:
        # Create Azure Chat Completion service
        chat_completion = AzureChatCompletion(
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )
        
        # Create a simple chat history
        chat_history = ChatHistory()
        chat_history.add_user_message("Hello, this is a test message. Please reply with 'Connection successful!'")
        
        print("Testing connection...")
        
        # Send a test message
        from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
        settings = AzureChatPromptExecutionSettings()
        response = await chat_completion.get_chat_message_content(chat_history, settings)
        
        if response:
            print("✅ Connection successful!")
            print(f"Response: {response.content}")
        else:
            print("❌ No response received")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_azure_openai_connection())
