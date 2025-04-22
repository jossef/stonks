"""
Storage functionality for the Stonks application.

This module provides functions for saving symbol data to files.
"""
import json
import logging
import os
from typing import Dict, Any

from stonks.models import SymbolData

logger = logging.getLogger(__name__)


def save_symbol_data(symbol_data: SymbolData, dist_dir: str) -> None:
    """
    Save symbol data to files in the distribution directory.
    
    Args:
        symbol_data: The symbol data to save
        dist_dir: The base distribution directory
    """
    try:
        # Create the symbol-specific directory
        symbol_dist_dir = os.path.join(dist_dir, symbol_data.config.id)
        os.makedirs(symbol_dist_dir, exist_ok=True)
        
        # Save price to a file
        with open(os.path.join(symbol_dist_dir, 'price'), 'w+') as f:
            f.write(str(symbol_data.price))
        
        # Save currency to a file
        with open(os.path.join(symbol_dist_dir, 'currency'), 'w+') as f:
            f.write(symbol_data.config.currency)
        
        # Save date to a file
        with open(os.path.join(symbol_dist_dir, 'date'), 'w+') as f:
            f.write(symbol_data.price_date)
        
        # Save all data to a JSON file
        with open(os.path.join(symbol_dist_dir, 'info.json'), 'w+') as f:
            json.dump(symbol_data.to_dict(), f)
            
        logger.debug(f"Symbol data for {symbol_data.config.id} saved successfully")
        
    except Exception as e:
        logger.error(f"Failed to save symbol data for {symbol_data.config.id}: {e}")
        raise