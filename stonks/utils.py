"""
Utility functions for the Stonks application.

This module provides various helper functions used throughout the application.
"""
import glob
import json
import logging
import os
import requests
from typing import List, Optional

from stonks.models import SymbolConfig


def setup_logging() -> None:
    """
    Set up logging configuration for the application.
    """
    # Suppress verbose logs from external libraries
    logging.getLogger("seleniumwire").setLevel(logging.ERROR)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def load_symbol_configs(symbols_dir: str) -> List[SymbolConfig]:
    """
    Load symbol configurations from JSON files in the specified directory.
    
    Args:
        symbols_dir: Directory containing symbol configuration files
        
    Returns:
        List of SymbolConfig objects
    """
    symbol_configs = []
    
    # Find all JSON files in the symbols directory
    symbol_files = glob.glob(os.path.join(symbols_dir, '*.json'))
    
    for symbol_file in symbol_files:
        try:
            with open(symbol_file, 'r') as f:
                symbol_data = json.load(f)
                symbol_config = SymbolConfig.from_dict(symbol_data)
                symbol_configs.append(symbol_config)
        except Exception as e:
            logging.error(f"Failed to load symbol configuration from {symbol_file}: {e}")
    
    return symbol_configs


def get_latest_user_agent(operating_system: str = 'windows', browser: str = 'chrome') -> Optional[str]:
    """
    Get the latest user agent string for the specified operating system and browser.
    
    Args:
        operating_system: The operating system (default: 'windows')
        browser: The browser (default: 'chrome')
        
    Returns:
        User agent string or None if not found
    """
    try:
        url = 'https://jnrbsn.github.io/user-agents/user-agents.json'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        user_agents = response.json()
        
        for user_agent in user_agents:
            if (operating_system.lower() in user_agent.lower() and 
                browser.lower() in user_agent.lower()):
                return user_agent
        
        return None
    except Exception as e:
        logging.error(f"Failed to get latest user agent: {e}")
        return None