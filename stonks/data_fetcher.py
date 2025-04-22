"""
Data fetching functionality for the Stonks application.

This module provides classes for fetching financial data from different sources.
"""
import abc
import datetime
import json
import logging
import time
from typing import Dict, Any, Optional

import brotli
import requests
import yfinance as yf
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver

from stonks.models import SymbolConfig, SymbolData
from stonks.utils import get_latest_user_agent

logger = logging.getLogger(__name__)


class DataFetcher(abc.ABC):
    """Base class for data fetchers."""
    
    def __init__(self, symbol_config: SymbolConfig):
        """
        Initialize the data fetcher.
        
        Args:
            symbol_config: Configuration for the symbol to fetch
        """
        self.symbol_config = symbol_config
    
    @abc.abstractmethod
    def fetch_data(self) -> SymbolData:
        """
        Fetch data for the symbol.
        
        Returns:
            Symbol data including price and date
        """
        pass


class JustETFDataFetcher(DataFetcher):
    """Data fetcher for JustETF."""
    
    def fetch_data(self) -> SymbolData:
        """
        Fetch data from JustETF.
        
        Returns:
            Symbol data including price and date
        """
        logger.info(f"Fetching data for {self.symbol_config.symbol} from JustETF")
        
        try:
            user_agent = get_latest_user_agent() or "Mozilla/5.0"
            url = (f'https://www.justetf.com/api/etfs/{self.symbol_config.symbol}/quote'
                   f'?locale=en&currency={self.symbol_config.currency}'
                   f'&isin={self.symbol_config.symbol}')
            
            response = requests.get(
                url, 
                headers={
                    'User-Agent': user_agent, 
                    'Accept': 'application/json'
                },
                timeout=30
            )
            response.raise_for_status()
            
            symbol_info = response.json()
            price = symbol_info['latestQuote']['raw']
            price_date = symbol_info['latestQuoteDate']
            
            return SymbolData(
                config=self.symbol_config,
                price=price,
                price_date=price_date
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch data from JustETF: {e}")
            raise


class YahooFinanceDataFetcher(DataFetcher):
    """Data fetcher for Yahoo Finance."""
    
    def fetch_data(self) -> SymbolData:
        """
        Fetch data from Yahoo Finance.
        
        Returns:
            Symbol data including price and date
        """
        logger.info(f"Fetching data for {self.symbol_config.symbol} from Yahoo Finance")
        
        try:
            ticker = yf.Ticker(self.symbol_config.symbol)
            history = ticker.history()
            
            if history.empty:
                raise ValueError(f"No data found for {self.symbol_config.symbol}")
            
            price = history['Close'].iloc[-1]
            price_date_obj = history['Close'].index[-1]
            price_date = datetime.datetime.strftime(price_date_obj, '%Y-%m-%d')
            
            return SymbolData(
                config=self.symbol_config,
                price=price,
                price_date=price_date
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch data from Yahoo Finance: {e}")
            raise


class IssaDataFetcher(DataFetcher):
    """Data fetcher for Israeli Stock Exchange (ISSA)."""
    
    def fetch_data(self) -> SymbolData:
        """
        Fetch data from Israeli Stock Exchange.
        
        Returns:
            Symbol data including price and date
        """
        logger.info(f"Fetching data for {self.symbol_config.symbol} from ISSA")
        
        # Ensure chromedriver is installed
        chromedriver_autoinstaller.install()
        
        # Initialize variables
        price = None
        price_date = None
        
        # Try multiple times with increasing wait times
        for attempt in range(1, 4):
            if price:
                break
                
            logger.info(f"Attempt {attempt} to fetch data from ISSA")
            
            try:
                # Set up Chrome options
                options = Options()
                options.add_argument("--headless=new")
                options.add_argument("--window-size=1920,980")
                
                # Create the driver
                driver = webdriver.Chrome(options=options)
                
                # Determine the URL based on the symbol type
                if self.symbol_config.type == 'etf':
                    url = f"https://market.tase.co.il/he/market_data/security/{self.symbol_config.symbol}"
                else:
                    url = f"https://maya.tase.co.il/he/funds/mutual-funds/{self.symbol_config.symbol}"
                
                # Navigate to the URL
                driver.get(url)
                
                # Wait for the page to load
                wait_time = 10 * attempt
                time.sleep(wait_time)
                driver.implicitly_wait(wait_time)
                
                # Process the requests to find the data
                for request in driver.requests:
                    if not request.response:
                        continue
                        
                    if request.url.startswith('https://api.tase.co.il/api/company/securitydata'):
                        response = self._get_issa_rest_api_response(request)
                        price = response['LastRate'] / 100  # ILA -> ILS
                        price_date = response['TradeDate']
                        price_date = datetime.datetime.strptime(price_date, "%d/%m/%Y").strftime('%Y-%m-%d')
                        break
                        
                    if request.url.startswith('https://maya.tase.co.il/api/v1/funds/mutual'):
                        response = self._get_issa_rest_api_response(request)
                        price = response['purchasePrice'] / 100  # ILA -> ILS
                        price_date = response['ratesAsOf']
                        price_date = datetime.datetime.strptime(price_date, "%Y-%m-%d").strftime('%Y-%m-%d')
                        break
                
                # Clean up
                driver.quit()
                
            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {e}")
                if driver:
                    driver.quit()
        
        if not price:
            raise ValueError(f"Failed to get price for {self.symbol_config.symbol} after multiple attempts")
        
        return SymbolData(
            config=self.symbol_config,
            price=price,
            price_date=price_date
        )
    
    def _get_issa_rest_api_response(self, request) -> Dict[str, Any]:
        """
        Extract and parse the response from an ISSA API request.
        
        Args:
            request: The request object from selenium-wire
            
        Returns:
            Parsed JSON response
        """
        if 400 <= request.response.status_code < 600:
            raise ValueError(f'Status code {request.response.status_code}')
        
        response = brotli.decompress(request.response.body)
        response = response.decode('utf-8')
        return json.loads(response)


def get_data_fetcher(symbol_config: SymbolConfig) -> DataFetcher:
    """
    Factory function to get the appropriate data fetcher for a symbol.
    
    Args:
        symbol_config: Configuration for the symbol
        
    Returns:
        A data fetcher instance for the symbol
        
    Raises:
        ValueError: If the source is not supported
    """
    if symbol_config.source == 'justetf':
        return JustETFDataFetcher(symbol_config)
    elif symbol_config.source == 'yahoo_finance':
        return YahooFinanceDataFetcher(symbol_config)
    elif symbol_config.source == 'issa':
        return IssaDataFetcher(symbol_config)
    else:
        raise ValueError(f"Unsupported source: {symbol_config.source}")