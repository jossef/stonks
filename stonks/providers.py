"""Data providers for different sources."""
from abc import ABC, abstractmethod
from datetime import datetime
import json
import logging
import time
from typing import Optional

import brotli
import requests
import yfinance as yf
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver

from .config import config
from .models import PriceData

logger = logging.getLogger(__name__)

class DataProvider(ABC):
    """Abstract base class for data providers."""
    
    @abstractmethod
    def get_price_data(self, symbol: str, currency: str) -> PriceData:
        """Get price data for a symbol."""
        pass

class JustETFProvider(DataProvider):
    """Provider for JustETF data."""
    
    def get_price_data(self, symbol: str, currency: str) -> PriceData:
        url = f'{config.JUSTETF_API_BASE_URL}/{symbol}/quote'
        params = {'locale': 'en', 'currency': currency, 'isin': symbol}
        
        response = requests.get(
            url,
            params=params,
            headers={'User-Agent': self._get_user_agent(), 'Accept': 'application/json'}
        )
        response.raise_for_status()
        data = response.json()
        
        return PriceData(
            symbol=symbol,
            price=data['latestQuote']['raw'],
            currency=currency,
            date=datetime.strptime(data['latestQuoteDate'], '%Y-%m-%d'),
            source='justetf'
        )

class YahooFinanceProvider(DataProvider):
    """Provider for Yahoo Finance data."""
    
    def get_price_data(self, symbol: str, currency: str) -> PriceData:
        ticker = yf.Ticker(symbol)
        history = ticker.history()
        
        return PriceData(
            symbol=symbol,
            price=history['Close'].iloc[-1],
            currency=currency,
            date=history.index[-1],
            source='yahoo_finance'
        )

class TASEProvider(DataProvider):
    """Provider for TASE (Tel Aviv Stock Exchange) data."""
    
    def get_price_data(self, symbol: str, currency: str) -> PriceData:
        for attempt in range(1, config.SELENIUM_MAX_RETRIES):
            try:
                price_data = self._get_price_with_selenium(symbol, attempt)
                if price_data:
                    return price_data
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {str(e)}")
                if attempt == config.SELENIUM_MAX_RETRIES - 1:
                    raise
        
        raise Exception(f"Failed to get price for {symbol} after {config.SELENIUM_MAX_RETRIES} attempts")

    def _get_price_with_selenium(self, symbol: str, attempt: int) -> Optional[PriceData]:
        options = Options()
        if config.SELENIUM_HEADLESS:
            options.add_argument("--headless=new")
        options.add_argument(f"--window-size={config.SELENIUM_WINDOW_SIZE[0]},{config.SELENIUM_WINDOW_SIZE[1]}")
        
        driver = webdriver.Chrome(options=options)
        try:
            url = f"{config.TASE_MARKET_URL}/{symbol}"
            driver.get(url)
            
            wait_time = config.SELENIUM_WAIT_TIME * attempt
            time.sleep(wait_time)
            driver.implicitly_wait(wait_time)
            
            for request in driver.requests:
                if not request.response:
                    continue
                    
                if request.url.startswith(f'{config.TASE_API_BASE_URL}/company/securitydata'):
                    try:
                        response = self._decode_response(request)
                        if response and 'LastRate' in response and 'TradeDate' in response:
                            return PriceData(
                                symbol=symbol,
                                price=response['LastRate'] / 100,  # ILA -> ILS
                                currency='ILS',
                                date=datetime.strptime(response['TradeDate'], "%d/%m/%Y"),
                                source='tase'
                            )
                        else:
                            logger.warning(f"Response missing required fields: {response}")
                    except Exception as e:
                        logger.warning(f"Error decoding response: {str(e)}")
                    
                if request.url.startswith('https://maya.tase.co.il/api/v1/funds/mutual'):
                    try:
                        response = self._decode_response(request)
                        if response and 'purchasePrice' in response and 'ratesAsOf' in response:
                            return PriceData(
                                symbol=symbol,
                                price=response['purchasePrice'] / 100,  # ILA -> ILS
                                currency='ILS',
                                date=datetime.strptime(response['ratesAsOf'], "%Y-%m-%d"),
                                source='tase'
                            )
                        else:
                            logger.warning(f"Response missing required fields: {response}")
                    except Exception as e:
                        logger.warning(f"Error decoding response: {str(e)}")
        finally:
            driver.quit()
        
        logger.warning(f"No valid price data found for symbol {symbol}")
        return None

    def _decode_response(self, request) -> dict:
        if 400 <= request.response.status_code < 600:
            raise Exception(f'Status code {request.response.status_code}')
        
        response = brotli.decompress(request.response.body)
        response = response.decode('utf-8')
        return json.loads(response)

    def _get_user_agent(self) -> str:
        response = requests.get(config.USER_AGENT_URL)
        response.raise_for_status()
        user_agents = response.json()
        
        for user_agent in user_agents:
            if 'windows' in user_agent.lower() and 'chrome' in user_agent.lower():
                return user_agent
        
        return None 