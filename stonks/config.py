"""
Configuration for the Stonks application.

This module provides configuration settings for the application.
"""
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration settings."""
    
    def __init__(self):
        """Initialize configuration with default values."""
        # Get the script directory (repository root)
        self.script_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        
        # Directory containing symbol configuration files
        self.symbols_dir = os.path.join(self.script_dir, 'symbols')
        
        # Directory for output files
        self.dist_dir = os.path.join(self.script_dir, 'dist')
        
        # Ensure the dist directory exists
        os.makedirs(self.dist_dir, exist_ok=True)
        
        # Default retry settings
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
        # Default timeout settings
        self.request_timeout = 30  # seconds
        
        # Default wait time for browser automation
        self.browser_wait_time = 10  # seconds