#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

def check_env_vars():
    print("Checking environment variables...")
    
    # Clear environment variables first to force reload
    for key in list(os.environ.keys()):
        if key.startswith('AZURE_OPENAI'):
            del os.environ[key]
    
    load_dotenv(override=True)
    
    required_vars = [
        'AZURE_OPENAI_CHAT_DEPLOYMENT_NAME',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_API_VERSION'
    ]
    
    print("\nEnvironment Variables:")
    print("-" * 50)
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Hide API key for security
            if 'KEY' in var:
                display_value = value[:8] + "..." + value[-4:] if len(value) > 12 else value
            else:
                display_value = value
            print(f"{var}: {display_value}")
        else:
            print(f"{var}: NOT SET")
            
    print("\nChecking .env file content:")
    print("-" * 50)
    try:
        with open('.env', 'r') as f:
            content = f.read()
            print(content)
    except FileNotFoundError:
        print(".env file not found!")

if __name__ == "__main__":
    check_env_vars()
