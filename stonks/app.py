"""Main application module for the Stonks application."""
import logging
import os
import chromedriver_autoinstaller
from typing import Dict, Type

from .config import config
from .models import SymbolTrackInfo, PriceData
from .providers import DataProvider, JustETFProvider, YahooFinanceProvider, TASEProvider
from .storage import Storage

# Suppress all noisy loggers
logging.getLogger("seleniumwire").setLevel(logging.ERROR)
logging.getLogger("selenium").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("chromedriver_autoinstaller").setLevel(logging.ERROR)
logging.getLogger("tensorflow").setLevel(logging.ERROR)
logging.getLogger("tensorflow.lite").setLevel(logging.ERROR)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logging

# Configure main logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Configure Selenium
chromedriver_autoinstaller.install()

class StonksApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        self.providers: Dict[str, Type[DataProvider]] = {
            'justetf': JustETFProvider,
            'yahoo_finance': YahooFinanceProvider,
            'issa': TASEProvider
        }
        self.storage = Storage()

    def process_symbol(self, symbol_file: str) -> None:
        """Process a single symbol file."""
        try:
            # Load symbol information
            track_info = self.storage.load_symbol_track_info(symbol_file)
            logger.info(f"Processing {symbol_file}...")
            
            # Get the appropriate provider
            provider_class = self.providers.get(track_info.source)
            if not provider_class:
                raise ValueError(f"Unknown data source: {track_info.source}")
            
            # Get price data
            provider = provider_class()
            price_data = provider.get_price_data(track_info.symbol, track_info.currency)
            
            # Save the data
            self.storage.save_price_data(track_info.id, price_data, track_info)
            
        except Exception as e:
            logger.exception(f"Failed to process {symbol_file}")
            raise

    def run(self) -> None:
        """Run the application."""
        logger.info(f"Reading symbols *.json files in {config.SYMBOLS_DIR}...")
        
        for symbol_file in self.storage.get_symbol_files():
            try:
                self.process_symbol(symbol_file)
            except Exception as e:
                logger.error(f"Failed to process {symbol_file}: {str(e)}")
                # Continue with next file even if one fails
                continue

def main():
    """Main entry point."""
    app = StonksApp()
    app.run()

if __name__ == '__main__':
    main() 