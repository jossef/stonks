import datetime
import glob
import json
import os
import brotli
import requests
import yfinance as yf
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver

chromedriver_autoinstaller.install()

CHROME_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SYMBOLS_DIR = os.path.join(SCRIPT_DIR, 'symbols')


def main():
    for symbol_track_file_path in glob.glob(os.path.join(SYMBOLS_DIR, '**', 'track.json'), recursive=True):

        with open(symbol_track_file_path) as f:
            symbol_track_info = json.load(f)

        symbol_price = 0
        symbol_price_date = ''

        symbol_id = symbol_track_info['id']
        symbol = symbol_track_info['symbol']
        currency = symbol_track_info['currency']

        if symbol_track_info['source'] == 'justetf':
            url = f'https://www.justetf.com/api/etfs/{symbol}/quote?locale=en&currency={currency}&isin={symbol}'
            r = requests.get(url, headers={'User-Agent': CHROME_USER_AGENT, 'Accept': 'application/json'})
            r.raise_for_status()
            symbol_info = r.json()
            symbol_price = symbol_info['latestQuote']['raw']
            symbol_price_date = symbol_info['latestQuoteDate']

        elif symbol_track_info['source'] == 'yahoo_finance':
            ticker_yahoo = yf.Ticker(symbol)
            symbol_track_info = ticker_yahoo.history()
            symbol_price = symbol_track_info['Close'].iloc[-1]
            symbol_price_date = symbol_track_info['Close'].index[-1]
            symbol_price_date = datetime.datetime.strftime(symbol_price_date, '%Y-%m-%d')

        elif symbol_track_info['source'] == 'issa':
            options = Options()
            options.add_argument("--headless=new")
            driver = webdriver.Chrome(options=options)
            driver.get(f"https://maya.tase.co.il/fund/{symbol}")
            driver.implicitly_wait(10)
            for request in driver.requests:
                if request.response:
                    if request.url.startswith('https://mayaapi.tase.co.il/api/fund/details'):
                        response = brotli.decompress(request.response.body)
                        response = response.decode('utf-8')
                        response = json.loads(response)
                        symbol_price = response['SellPrice']
                        symbol_price_date = response['RelevantDate']
                        symbol_price_date = datetime.datetime.fromisoformat(symbol_price_date).strftime('%Y-%m-%d')

        with open(os.path.join(os.path.dirname(symbol_track_file_path), 'price'), 'w+') as f:
            f.write(f'{symbol_price}')

        print(symbol_id, symbol_price_date, symbol_price, currency)


if __name__ == '__main__':
    main()
