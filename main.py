import datetime
import glob
import json
import logging
import os
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
    url = f'https://jnrbsn.github.io/user-agents/user-agents.json'
    r = requests.get(url)
    r.raise_for_status()
    user_agents = r.json()

    for user_agent in user_agents:
        if operating_system.lower() in user_agent.lower() and browser.lower() in user_agent.lower():
            return user_agent

    return None


def main():
    logging.info(f"reading symbols *.json files in {SYMBOLS_DIR} ...")
    for symbol_track_file_path in glob.glob(os.path.join(SYMBOLS_DIR, '*.json'), recursive=True):
        logging.info(f"processing {symbol_track_file_path} ...")

        try:
            with open(symbol_track_file_path) as f:
                symbol_track_info = json.load(f)

            symbol_price = 0
            symbol_price_date = ''

            symbol_id = symbol_track_info['id']
            symbol = symbol_track_info['symbol']
            currency = symbol_track_info['currency']
            user_agent_header = get_latest_user_agent(operating_system='windows', browser='chrome')

            if symbol_track_info['source'] == 'justetf':
                url = f'https://www.justetf.com/api/etfs/{symbol}/quote?locale=en&currency={currency}&isin={symbol}'
                r = requests.get(url, headers={'User-Agent': user_agent_header, 'Accept': 'application/json'})
                r.raise_for_status()
                symbol_info = r.json()
                symbol_price = symbol_info['latestQuote']['raw']
                symbol_price_date = symbol_info['latestQuoteDate']

            elif symbol_track_info['source'] == 'yahoo_finance':
                ticker_yahoo = yf.Ticker(symbol)
                symbol_info = ticker_yahoo.history()
                symbol_price = symbol_info['Close'].iloc[-1]
                symbol_price_date = symbol_info['Close'].index[-1]
                symbol_price_date = datetime.datetime.strftime(symbol_price_date, '%Y-%m-%d')

            elif symbol_track_info['source'] == 'issa':
                for _ in range(3):
                    if symbol_price:
                        break

                    options = Options()
                    options.add_argument("--headless=new")
                    driver = webdriver.Chrome(options=options)

                    if symbol_track_info['type'] == 'etf':
                        url = f"https://maya.tase.co.il/foreignetf/{symbol}"
                    else:
                        url = f"https://maya.tase.co.il/fund/{symbol}"

                    driver.get(url)
                    driver.implicitly_wait(10)
                    for request in driver.requests:
                        if request.response:
                            if request.url.startswith('https://mayaapi.tase.co.il/api/fund/details'):
                                response = get_issa_rest_api_response(request)
                                symbol_price = response['SellPrice'] / 100  # ILA -> ILS
                                symbol_price_date = response['RelevantDate']
                                symbol_price_date = datetime.datetime.fromisoformat(symbol_price_date).strftime('%Y-%m-%d')

                            if request.url.startswith('https://mayaapi.tase.co.il/api/foreignetf/tradedata'):
                                response = get_issa_rest_api_response(request)
                                symbol_price = response['LastRate'] / 100  # ILA -> ILS
                                symbol_price_date = response['TradeDate']
                                symbol_price_date = datetime.datetime.strptime(symbol_price_date, "%d/%m/%Y").strftime('%Y-%m-%d')

            if not symbol_price:
                raise Exception(f'Failed to get price for {symbol}')

            symbol_dist_dir = os.path.join(DIST_DIR, symbol_id)
            os.makedirs(symbol_dist_dir, exist_ok=True)
            symbol_track_info['price'] = symbol_price
            symbol_track_info['price_date'] = symbol_price_date

            with open(os.path.join(symbol_dist_dir, 'price'), 'w+') as f:
                f.write(str(symbol_price))

            with open(os.path.join(symbol_dist_dir, 'currency'), 'w+') as f:
                f.write(currency)

            with open(os.path.join(symbol_dist_dir, 'date'), 'w+') as f:
                f.write(symbol_price_date)

            with open(os.path.join(symbol_dist_dir, 'info.json'), 'w+') as f:
                json.dump(symbol_track_info, f)

            logging.info(f'symbol "{symbol_id}" update completed. price: {symbol_price} {currency} date: {symbol_price_date}')

        except Exception as e:
            logging.exception(f'Failed to process {symbol_track_file_path}')
            raise


def get_issa_rest_api_response(request):
    if 400 <= request.response.status_code < 600:
        raise Exception(f'Status code {request.response.status_code}')

    response = brotli.decompress(request.response.body)
    response = response.decode('utf-8')
    response = json.loads(response)
    return response


if __name__ == '__main__':
    main()
