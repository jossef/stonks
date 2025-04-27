"""Storage operations for the Stonks application."""
import json
import os
import logging
from typing import Dict, List

from .config import config
from .models import SymbolTrackInfo, PriceData

logger = logging.getLogger(__name__)

class Storage:
    """Handles data storage operations."""
    
    @staticmethod
    def load_symbol_track_info(file_path: str) -> SymbolTrackInfo:
        """Load symbol track info from a JSON file."""
        try:
            with open(file_path) as f:
                data = json.load(f)
            return SymbolTrackInfo.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load symbol track info from {file_path}: {str(e)}")
            raise

    @staticmethod
    def save_price_data(symbol_id: str, price_data: PriceData, track_info: SymbolTrackInfo) -> None:
        """Save price data and track info to the distribution directory."""
        symbol_dist_dir = os.path.join(config.DIST_DIR, symbol_id)
        os.makedirs(symbol_dist_dir, exist_ok=True)
        
        # Update track info with price data
        track_info.price = price_data.price
        track_info.price_date = price_data.formatted_date
        
        # Save individual files
        Storage._save_file(os.path.join(symbol_dist_dir, 'price'), str(price_data.price))
        Storage._save_file(os.path.join(symbol_dist_dir, 'currency'), price_data.currency)
        Storage._save_file(os.path.join(symbol_dist_dir, 'date'), price_data.formatted_date)
        
        # Save complete info
        with open(os.path.join(symbol_dist_dir, 'info.json'), 'w') as f:
            json.dump(track_info.to_dict(), f, indent=2)
        
        logger.info(
            f'Symbol "{symbol_id}" update completed. '
            f'Price: {price_data.price} {price_data.currency} '
            f'Date: {price_data.formatted_date}'
        )

    @staticmethod
    def _save_file(file_path: str, content: str) -> None:
        """Save content to a file."""
        try:
            with open(file_path, 'w') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {str(e)}")
            raise

    @staticmethod
    def get_symbol_files() -> List[str]:
        """Get all symbol JSON files from the symbols directory."""
        return [
            os.path.join(config.SYMBOLS_DIR, f)
            for f in os.listdir(config.SYMBOLS_DIR)
            if f.endswith('.json')
        ] 