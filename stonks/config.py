"""Configuration settings for the Stonks application."""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Application configuration settings."""
    # Directory paths
    SCRIPT_DIR: str = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    SYMBOLS_DIR: str = os.path.join(SCRIPT_DIR, 'symbols')
    DIST_DIR: str = os.path.join(SCRIPT_DIR, 'dist')
    
    # API settings
    USER_AGENT_URL: str = 'https://jnrbsn.github.io/user-agents/user-agents.json'
    JUSTETF_API_BASE_URL: str = 'https://www.justetf.com/api/etfs'
    TASE_API_BASE_URL: str = 'https://api.tase.co.il/api'
    TASE_MARKET_URL: str = 'https://market.tase.co.il/he/market_data/security'
    TASE_FUNDS_URL: str = 'https://maya.tase.co.il/he/funds/mutual-funds'
    
    # Selenium settings
    SELENIUM_HEADLESS: bool = True
    SELENIUM_WINDOW_SIZE: tuple = (1920, 980)
    SELENIUM_MAX_RETRIES: int = 10
    SELENIUM_WAIT_TIME: int = 30  # seconds
    
    # Logging settings
    LOG_LEVEL: str = 'INFO'
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Create a global config instance
config = Config() 