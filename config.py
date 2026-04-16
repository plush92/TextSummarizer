"""
Configuration Module

Handles API keys, settings, and configuration management for the text summarizer.
"""

import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


class Config:
    """Configuration manager for API keys and settings"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.path.join(Path.home(), '.text_summarizer_config')
        self.config_data = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables and config file"""
        
        # Load .env file if available
        if load_dotenv:
            load_dotenv()
        
        # Load from environment variables first (highest priority)
        self.config_data = {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'default_model': os.getenv('SUMMARIZER_DEFAULT_MODEL', 'openai'),
            'default_max_length': int(os.getenv('SUMMARIZER_MAX_LENGTH', '150')),
        }
        
        # Load from config file if it exists (lower priority)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = {}
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            file_config[key.strip()] = value.strip()
                    
                    # Only use file config if env var is not set
                    for key, value in file_config.items():
                        if key not in self.config_data or self.config_data[key] is None:
                            self.config_data[key] = value
                            
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key"""
        return self.config_data.get('openai_api_key')
    
    def get_anthropic_api_key(self) -> Optional[str]:
        """Get Anthropic API key"""  
        return self.config_data.get('anthropic_api_key')
    
    def get_default_model(self) -> str:
        """Get default model"""
        return self.config_data.get('default_model', 'openai')
    
    def get_default_max_length(self) -> int:
        """Get default maximum summary length"""
        return int(self.config_data.get('default_max_length', 150))
    
    def create_config_file(self):
        """Create a sample configuration file"""
        config_template = f"""# Text Summarizer Configuration
# You can set API keys here instead of environment variables
# Environment variables take precedence over this file

# OpenAI Configuration
openai_api_key=your_openai_api_key_here

# Anthropic Configuration  
anthropic_api_key=your_anthropic_api_key_here

# Default Settings
default_model=openai
default_max_length=150
"""
        
        try:
            with open(self.config_file, 'w') as f:
                f.write(config_template)
            print(f"Created config file: {self.config_file}")
            print("Please edit the file to add your API keys.")
        except Exception as e:
            print(f"Error creating config file: {e}")
    
    def set_api_key(self, provider: str, api_key: str):
        """Set API key for a provider"""
        key_name = f"{provider}_api_key"
        self.config_data[key_name] = api_key
        
        # Update config file
        self._update_config_file(key_name, api_key)
    
    def _update_config_file(self, key: str, value: str):
        """Update a specific key in the config file"""
        config_lines = []
        key_found = False
        
        # Read existing config
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_lines = f.readlines()
            except Exception:
                pass
        
        # Update or add the key
        for i, line in enumerate(config_lines):
            if line.strip().startswith(f"{key}="):
                config_lines[i] = f"{key}={value}\n"
                key_found = True
                break
        
        # Add key if not found
        if not key_found:
            config_lines.append(f"{key}={value}\n")
        
        # Write back to file
        try:
            with open(self.config_file, 'w') as f:
                f.writelines(config_lines)
        except Exception as e:
            print(f"Error updating config file: {e}")
    
    def validate_model_config(self, model_type: str) -> bool:
        """Validate that the required API key is available for the model type"""
        if model_type == 'openai':
            return bool(self.get_openai_api_key())
        elif model_type == 'anthropic':
            return bool(self.get_anthropic_api_key())
        elif model_type == 'local':
            return True  # No API key needed for local model
        else:
            return False
    
    def get_missing_config_help(self, model_type: str) -> str:
        """Get help message for missing configuration"""
        if model_type == 'openai':
            return """
OpenAI API key not configured. You can set it by:

1. Environment variable:
   export OPENAI_API_KEY="your_api_key_here"

2. Config file:
   Run: python main.py --setup
   Then edit: ~/.text_summarizer_config

3. Get an API key at: https://platform.openai.com/api-keys
"""
        
        elif model_type == 'anthropic':
            return """
Anthropic API key not configured. You can set it by:

1. Environment variable:
   export ANTHROPIC_API_KEY="your_api_key_here"

2. Config file:
   Run: python main.py --setup
   Then edit: ~/.text_summarizer_config

3. Get an API key at: https://console.anthropic.com/
"""
        
        else:
            return f"Unknown model type: {model_type}"


def setup_config():
    """Interactive setup for configuration"""
    config = Config()
    
    print("=" * 50)
    print("Text Summarizer Configuration Setup")
    print("=" * 50)
    
    print("\nThis tool supports multiple AI providers:")
    print("1. OpenAI GPT (recommended)")
    print("2. Anthropic Claude")
    print("3. Local processing (basic, no API key needed)")
    
    # Check existing configuration
    has_openai = bool(config.get_openai_api_key())
    has_anthropic = bool(config.get_anthropic_api_key())
    
    print(f"\nCurrent configuration:")
    print(f"  OpenAI API Key: {'✓ Configured' if has_openai else '✗ Not set'}")
    print(f"  Anthropic API Key: {'✓ Configured' if has_anthropic else '✗ Not set'}")
    
    if not has_openai and not has_anthropic:
        print("\n⚠️  No API keys configured. You can:")
        print("1. Use local processing (limited functionality)")
        print("2. Set up API keys for better results")
        
        choice = input("\nWould you like to set up API keys? (y/n): ").lower().strip()
        
        if choice == 'y':
            # Create config file
            config.create_config_file()
            print(f"\nPlease edit the config file: {config.config_file}")
            print("Add your API keys, then run the tool again.")
        else:
            print("Using local processing mode.")
    else:
        print("\n✓ Configuration looks good!")
    
    print("\nSetup complete!")


if __name__ == "__main__":
    setup_config()