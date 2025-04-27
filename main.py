import datetime
import glob
import json
import logging
import os
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import chromedriver_autoinstaller

chromedriver_autoinstaller.install()
from dotenv import load_dotenv

load_dotenv()
import time
import brotli
import requests
import yfinance as yf
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver

logging.getLogger("seleniumwire").setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

chromedriver_autoinstaller.install()

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SYMBOLS_DIR = os.path.join(SCRIPT_DIR, 'symbols')
DIST_DIR = os.path.join(SCRIPT_DIR, 'dist')


def get_latest_user_agent(operating_system='windows', browser='chrome'):
    """
    Fetch the latest user agent string for the specified operating system and browser.
    """
    url = f'https://jnrbsn.github.io/user-agents/user-agents.json'
    response = requests.get(url)
    response.raise_for_status()
    user_agents = response.json()

    for user_agent in user_agents:
        if operating_system.lower() in user_agent.lower() and browser.lower() in user_agent.lower():
            return user_agent

    return None


def process_symbol_file(symbol_track_info, user_agent_header):
    """
    Process a single symbol file and fetch its price and date.
    """
    symbol_price = 0
    symbol_price_date = ''

    symbol_id = symbol_track_info['id']
    symbol = symbol_track_info['symbol']
    currency = symbol_track_info['currency']

    if symbol_track_info['source'] == 'justetf':
        symbol_price, symbol_price_date = fetch_price_from_justetf(symbol, currency, user_agent_header)

    elif symbol_track_info['source'] == 'yahoo_finance':
        symbol_price, symbol_price_date = fetch_price_from_yahoo_finance(symbol)

    elif symbol_track_info['source'] == 'issa':
        symbol_price, symbol_price_date = fetch_price_from_issa(symbol_track_info, user_agent_header)

    if not symbol_price:
        raise Exception(f'Failed to get price for {symbol}')

    return symbol_price, symbol_price_date


def fetch_price_from_justetf(symbol: str, currency: str, user_agent_header: str):
    """
    Fetch the price from the justetf source.
    """
    """
    Fetch the price from the justetf source.
    :param symbol: The symbol to fetch the price for.
    :param currency: The currency of the symbol.
    :param user_agent_header: The user agent header to use for the request.
    """
    url = f'https://www.justetf.com/api/etfs/{symbol}/quote?locale=en&currency={currency}&isin={symbol}'
    response = requests.get(url, headers={'User-Agent': user_agent_header, 'Accept': 'application/json'})
    response.raise_for_status()
    symbol_info = response.json()
    symbol_price = symbol_info['latestQuote']['raw']
    symbol_price_date = symbol_info['latestQuoteDate']

    return symbol_price, symbol_price_date


def fetch_price_from_yahoo_finance(symbol: str):
    """
    Fetch the price from the yahoo_finance source.
    
    :param symbol: The symbol to fetch the price for.
    :return: A tuple containing the symbol price and the date of the price.
    """
    ticker_yahoo = yf.Ticker(symbol)
    symbol_info = ticker_yahoo.history()
    symbol_price = symbol_info['Close'].iloc[-1]
    symbol_price_date = symbol_info['Close'].index[-1]
    symbol_price_date = datetime.datetime.strftime(symbol_price_date, '%Y-%m-%d')

    return symbol_price, symbol_price_date


def fetch_price_from_issa(symbol_track_info: dict, user_agent_header: str):
    """
    Fetch the price from the issa source using Selenium.
    
    :param symbol_track_info: The symbol track information.
    :param user_agent_header: The user agent header to use for the request.
    :return: A tuple containing the symbol price and the date of the price.
    """
    symbol_price = None
    symbol_price_date = ''

    for attempt in range(1, 10):
        if symbol_price:
            break

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,980")
        driver_path = os.getenv('CHROMEDRIVER_PATH')
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)

        if symbol_track_info['type'] == 'etf':
            url = f"https://market.tase.co.il/he/market_data/security/{symbol_track_info['symbol']}"
        else:
            url = f"https://maya.tase.co.il/he/funds/mutual-funds/{symbol_track_info['symbol']}"

        driver.get(url)
        time.sleep(30 * attempt)
        driver.implicitly_wait(30 * attempt)
        for request in driver.requests:
            if request.response:
                if request.url.startswith('https://api.tase.co.il/api/company/securitydata'):
                    response = get_issa_rest_api_response(request)
                    symbol_price = response['LastRate'] / 100  # ILA -> ILS
                    symbol_price_date = response['TradeDate']
                    symbol_price_date = datetime.datetime.strptime(symbol_price_date, "%d/%m/%Y").strftime('%Y-%m-%d')

                if request.url.startswith('https://maya.tase.co.il/api/v1/funds/mutual'):
                    response = get_issa_rest_api_response(request)
                    symbol_price = response['purchasePrice'] / 100  # ILA -> ILS
                    symbol_price_date = response['ratesAsOf']
                    symbol_price_date = datetime.datetime.strptime(symbol_price_date, "%Y-%m-%d").strftime('%Y-%m-%d')

    return symbol_price, symbol_price_date


def main():
    """
    Main entry point for the script. Reads and processes symbol files.
    """
    # Load environment variables
    symbols_dir = os.getenv('SYMBOLS_DIR')
    dist_dir = os.getenv('DIST_DIR')

    # Log the start of reading symbol files
    logging.info(f"Reading symbols *.json files in {symbols_dir} ...")

    # Iterate over all symbol JSON files in the SYMBOLS_DIR
    for symbol_file_path in glob.glob(os.path.join(SYMBOLS_DIR, '*.json'), recursive=True):
        # Log the processing of the current symbol file
        logging.info(f"Processing {symbol_file_path} ...")

        try:
            # Load the symbol track information from the JSON file
            with open(symbol_file_path) as file:
                symbol_info = json.load(file)

            # Get the latest user agent header
            user_agent_header = get_latest_user_agent(operating_system='windows', browser='chrome')

            # Fetch the symbol price and date
            symbol_price, symbol_price_date = process_symbol_file(symbol_info, user_agent_header)

            # Define the distribution directory for the symbol
            symbol_dist_directory = os.path.join(dist_dir, symbol_info['id'])
            os.makedirs(symbol_dist_directory, exist_ok=True)

            # Update the symbol track information with the fetched price and date
            symbol_info['price'] = symbol_price
            symbol_info['price_date'] = symbol_price_date

            # Write the fetched price to a file
            try:
                with open(os.path.join(symbol_dist_directory, 'price'), 'w+') as price_file:
                    price_file.write(str(symbol_price))
            except Exception as e:
                logging.error(f'Failed to write price to file: {e}')
                raise

            # Write the currency to a file
            try:
                with open(os.path.join(symbol_dist_directory, 'currency'), 'w+') as currency_file:
                    currency_file.write(symbol_info['currency'])
            except Exception as e:
                logging.error(f'Failed to write currency to file: {e}')
                raise

            # Write the fetched date to a file
            try:
                with open(os.path.join(symbol_dist_directory, 'date'), 'w+') as date_file:
                    date_file.write(symbol_price_date)
            except Exception as e:
                logging.error(f'Failed to write date to file: {e}')
                raise

            # Write the updated symbol track information to a JSON file
            try:
                with open(os.path.join(symbol_dist_directory, 'info.json'), 'w+') as info_file:
                    json.dump(symbol_info, info_file)
            except Exception as e:
                logging.error(f'Failed to write info.json to file: {e}')
                raise

            # Log the completion of processing the symbol
            logging.info(f'Symbol "{symbol_info["id"]}" update completed. Price: {symbol_price} {symbol_info["currency"]} Date: {symbol_price_date}')

        except Exception as e:
            # Log and re-raise any exceptions that occur during processing
            logging.exception(f'Failed to process {symbol_file_path}')
            raise


def get_issa_rest_api_response(request):
    """
    Decompress and parse the response body from the issa REST API.
    """
    if 400 <= request.response.status_code < 600:
        raise Exception(f'Status code {request.response.status_code}')

    response = brotli.decompress(request.response.body)
    response = response.decode('utf-8')
    response = json.loads(response)
    return response


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.exception(f'Main function failed: {e}')
        raise  # Re-raise the exception to ensure it is not silenced
    finally:
        logging.info('Script execution completed.')
