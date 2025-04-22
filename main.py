#!/usr/bin/env python3
"""
Stonks - A tool for tracking stock and fund prices from various sources.

This script fetches financial data from different sources and makes it available
for use in Google Sheets or other applications.
"""
import logging
import sys
from typing import List

from stonks.config import Config
from stonks.data_fetcher import get_data_fetcher
from stonks.models import SymbolConfig
from stonks.storage import save_symbol_data
from stonks.utils import setup_logging, load_symbol_configs

def main() -> None:
    """
    Main entry point for the Stonks application.

    Reads symbol configurations, fetches price data, and saves the results.
    """
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Initialize configuration
        config = Config()

        # Load symbol configurations
        logger.info(f"Reading symbols *.json files in {config.symbols_dir} ...")
        symbol_configs = load_symbol_configs(config.symbols_dir)

        if not symbol_configs:
            logger.error("No symbol configurations found. Exiting.")
            sys.exit(1)

        # Process each symbol
        for symbol_config in symbol_configs:
            process_symbol(symbol_config, config)

        logger.info("All symbols processed successfully.")

    except Exception as e:
        logger.exception(f"An error occurred during execution: {e}")
        sys.exit(1)

def process_symbol(symbol_config: SymbolConfig, config: Config) -> None:
    """
    Process a single symbol configuration.

    Args:
        symbol_config: The symbol configuration to process
        config: The application configuration
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Processing symbol {symbol_config.id} ({symbol_config.symbol})...")

        # Get the appropriate data fetcher for this symbol
        data_fetcher = get_data_fetcher(symbol_config)

        # Fetch the price data
        symbol_data = data_fetcher.fetch_data()

        if not symbol_data.price:
            raise ValueError(f"Failed to get price for {symbol_config.symbol}")

        # Save the data
        save_symbol_data(symbol_data, config.dist_dir)

        logger.info(
            f'Symbol "{symbol_config.id}" update completed. '
            f'Price: {symbol_data.price} {symbol_config.currency} '
            f'Date: {symbol_data.price_date}'
        )

    except Exception as e:
        logger.error(f"Failed to process symbol {symbol_config.id}: {e}")
        # Continue processing other symbols instead of raising the exception

if __name__ == "__main__":
    main()
