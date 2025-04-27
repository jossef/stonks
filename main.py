import datetime
import glob
import json
import logging
import os
import time
from typing import Optional, Dict, Any

import requests
import yfinance as yf
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver

try:
    import brotli
except ImportError:
    brotli = None  # Will error if issa scraping needed but brotli missing

# Logging config
logging.getLogger("seleniumwire").setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Install ChromeDriver if needed for issa scraping
chromedriver_autoinstaller.install()

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SYMBOLS_DIR = os.path.join(SCRIPT_DIR, "symbols")
DIST_DIR = os.path.join(SCRIPT_DIR, "dist")


def get_latest_user_agent(operating_system: str = "windows", browser: str = "chrome") -> Optional[str]:
    """Fetches latest user agent for specified OS/browser."""
    url = "https://jnrbsn.github.io/user-agents/user-agents.json"
    response = requests.get(url)
    response.raise_for_status()
    user_agents = response.json()

    for ua in user_agents:
        if operating_system.lower() in ua.lower() and browser.lower() in ua.lower():
            return ua
    return None


def fetch_justetf(symbol_track_info: dict, user_agent: Optional[str]) -> tuple:
    """Fetch price and date from justetf."""
    url = (
        f"https://www.justetf.com/api/etfs/{symbol_track_info['symbol']}/quote"
        f"?locale=en&currency={symbol_track_info['currency']}&isin={symbol_track_info['symbol']}"
    )
    resp = requests.get(
        url,
        headers={"User-Agent": user_agent or "", "Accept": "application/json"}
    )
    resp.raise_for_status()
    data = resp.json()
    return data["latestQuote"]["raw"], data["latestQuoteDate"]


def fetch_yahoo(symbol_track_info: dict) -> tuple:
    """Fetch price and date from Yahoo Finance using yfinance."""
    ticker = yf.Ticker(symbol_track_info["symbol"])
    hist = ticker.history()
    price = hist["Close"].iloc[-1]
    price_date = hist["Close"].index[-1]
    price_date = datetime.datetime.strftime(price_date, "%Y-%m-%d")
    return price, price_date


def fetch_issa(symbol_track_info: dict, max_attempts: int = 9) -> tuple:
    """Fetch price and date from Israeli sources using Selenium."""
    if brotli is None:
        raise ImportError("brotli module required for ISSA scraping but not installed.")

    for attempt in range(1, max_attempts + 1):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,980")
        driver = webdriver.Chrome(options=options)

        try:
            url = (
                f"https://market.tase.co.il/he/market_data/security/{symbol_track_info['symbol']}"
                if symbol_track_info["type"] == "etf"
                else f"https://maya.tase.co.il/he/funds/mutual-funds/{symbol_track_info['symbol']}"
            )
            driver.get(url)
            wait_time = 30 * attempt
            time.sleep(wait_time)
            driver.implicitly_wait(wait_time)

            for req in driver.requests:
                if not req.response:
                    continue
                if req.url.startswith("https://api.tase.co.il/api/company/securitydata"):
                    resp_json = parse_issa_response(req)
                    price = resp_json["LastRate"] / 100
                    price_date = datetime.datetime.strptime(
                        resp_json["TradeDate"], "%d/%m/%Y"
                    ).strftime("%Y-%m-%d")
                    return price, price_date

                if req.url.startswith("https://maya.tase.co.il/api/v1/funds/mutual"):
                    resp_json = parse_issa_response(req)
                    price = resp_json["purchasePrice"] / 100
                    price_date = datetime.datetime.strptime(
                        resp_json["ratesAsOf"], "%Y-%m-%d"
                    ).strftime("%Y-%m-%d")
                    return price, price_date

        finally:
            driver.quit()

    raise Exception(f"Failed to get ISSA price for {symbol_track_info['symbol']} after {max_attempts} attempts")


def parse_issa_response(request) -> dict:
    """Decompress and decode brotli response JSON from seleniumwire request."""
    resp = request.response
    if 400 <= resp.status_code < 600:
        raise Exception(f"HTTP error {resp.status_code} from ISSA API.")
    body = brotli.decompress(resp.body)
    return json.loads(body.decode("utf-8"))


def process_symbol_json(json_path: str) -> None:
    """Given a symbol JSON file, fetch and update price info."""
    logging.info(f"Processing {json_path} ...")
    with open(json_path) as f:
        symbol_info = json.load(f)

    symbol_id = symbol_info["id"]
    currency = symbol_info["currency"]
    price, date = None, None

    user_agent = get_latest_user_agent(operating_system="windows", browser="chrome") if symbol_info["source"] == "justetf" else None

    try:
        if symbol_info["source"] == "justetf":
            price, date = fetch_justetf(symbol_info, user_agent)
        elif symbol_info["source"] == "yahoo_finance":
            price, date = fetch_yahoo(symbol_info)
        elif symbol_info["source"] == "issa":
            price, date = fetch_issa(symbol_info)
        else:
            raise ValueError(f"Unknown source: {symbol_info['source']}")
    except Exception as exc:
        logging.exception(f"Failed to fetch price for {symbol_id}")
        raise

    if not price:
        raise Exception(f"Price not found for {symbol_id}")

    # Update info and write out
    symbol_info.update({"price": price, "price_date": date})
    symbol_dist_dir = os.path.join(DIST_DIR, symbol_id)
    os.makedirs(symbol_dist_dir, exist_ok=True)
    output_files = {
        "price": str(price),
        "currency": currency,
        "date": date,
        "info.json": json.dumps(symbol_info, ensure_ascii=False, indent=2),
    }

    for fname, contents in output_files.items():
        outpath = os.path.join(symbol_dist_dir, fname)
        mode = "w" if not fname.endswith(".json") else "w"
        with open(outpath, mode, encoding="utf-8") as f:
            f.write(contents)

    logging.info(
        f'Symbol "{symbol_id}" updated: price={price} {currency}, date={date}'
    )


def main():
    """Entrypoint: process all symbol jsons in symbols/."""
    symbol_files = glob.glob(os.path.join(SYMBOLS_DIR, "*.json"), recursive=True)
    if not symbol_files:
        logging.warning("No symbol definition files found.")
        return
    logging.info(f"Found {len(symbol_files)} symbol files in {SYMBOLS_DIR}")
    errors = []
    for path in symbol_files:
        try:
            process_symbol_json(path)
        except Exception as exc:
            logging.error(f"Failed to process '{path}': {exc}")
            errors.append(path)
    if errors:
        logging.warning(f"Failed to process {len(errors)} symbols. See log for details.")


if __name__ == "__main__":
    main()
