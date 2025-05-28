import requests
import time
import os
from sqlalchemy.orm import Session
from ..models import Stock # Assuming models.py is in the same directory as __init__.py for app
from .. import db # To access the db instance for session creation if needed, or pass session directly

PREDEFINED_STOCKS = [
    "PETR4.SAO", "VALE3.SAO", "ITUB4.SAO", "ABEV3.SAO", "MGLU3.SAO",
    "BBDC4.SAO", "WEGE3.SAO", "RENT3.SAO", "RADL3.SAO", "LREN3.SAO",
    "BBAS3.SAO", "GGBR4.SAO", "SUZB3.SAO", "ITSA4.SAO", "B3SA3.SAO"
]

ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

def fetch_and_store_stock_details(db_session: Session, api_key: str):
    """
    Fetches stock overview information from Alpha Vantage for a predefined list
    of B3 tickers and stores them in the database if they don't already exist.
    """
    print("Starting to fetch and store stock details...")

    for ticker in PREDEFINED_STOCKS:
        print(f"Processing {ticker}...")

        # Check if stock already exists
        existing_stock = db_session.query(Stock).filter_by(ticker=ticker).first()
        if existing_stock:
            print(f"  Stock {ticker} already exists in the database. Skipping.")
            continue

        params = {
            "function": "OVERVIEW",
            "symbol": ticker,
            "apikey": api_key
        }

        try:
            response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            # Check for empty or error response from Alpha Vantage
            if not data or "Symbol" not in data or data.get("Symbol") != ticker:
                # API might return an empty dict or a dict with an error message for invalid symbols or if limit is hit
                print(f"  Could not retrieve valid data for {ticker}. Response: {data.get('Information', data)}")
                if "Note" in data or "Information" in data : # Often indicates API limit or invalid symbol
                     print(f"  API Note/Information for {ticker}: {data.get('Note', data.get('Information'))}")
                     if "call frequency" in data.get('Note',data.get('Information','')).lower():
                        print("  API call frequency limit likely reached. Aborting further API calls.")
                        break # Stop trying to fetch more data
                # Wait before next call even if this one failed, to avoid hammering the API
                time.sleep(15)
                continue


            new_stock = Stock(
                ticker=ticker,
                name=data.get("Name"),
                sector=data.get("Sector"),
                industry=data.get("Industry"),
                logo_url=None  # Alpha Vantage OVERVIEW doesn't provide a logo URL
            )
            db_session.add(new_stock)
            db_session.commit()
            print(f"  Successfully fetched and stored {ticker} ({data.get('Name')}).")

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching data for {ticker}: {e}")
        except Exception as e: # Catch any other unexpected errors e.g. during DB interaction
            print(f"  An unexpected error occurred while processing {ticker}: {e}")
            db_session.rollback() # Rollback in case of error during commit

        # Respect API rate limits (e.g., 5 calls per minute for free tier)
        # No sleep after the last stock in the list
        if ticker != PREDEFINED_STOCKS[-1]: # Only sleep if it's not the last item
            print("  Waiting 15 seconds before next API call for stock details...")
            time.sleep(15)

    print("Finished fetching and storing stock details.")


def fetch_and_store_historical_prices(db_session: Session, api_key: str, stock_ticker: str, stock_id):
    """
    Fetches and stores historical daily price data for a given stock.
    Returns True if successful or data already up-to-date, False on API error/limit.
    """
    print(f"Fetching historical prices for {stock_ticker} (ID: {stock_id})...")
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": stock_ticker,
        "outputsize": "full", # "compact" for last 100, "full" for full history
        "apikey": api_key
    }
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if "Error Message" in data:
            print(f"  API Error for {stock_ticker}: {data['Error Message']}")
            return False
        if "Note" in data: # Indicates potential rate limiting
            print(f"  API Note for {stock_ticker}: {data['Note']}")
            if "call frequency" in data['Note'].lower():
                 print(f"  Rate limit likely hit for {stock_ticker}.")
                 return False # Indicate rate limit issue

        time_series = data.get("Time Series (Daily)")
        if not time_series:
            print(f"  No 'Time Series (Daily)' data found for {stock_ticker}. Response: {data}")
            return True # No data to process, but not an API error per se

        from datetime import datetime # Import here to keep it local if needed
        from decimal import Decimal # For price data
        from ..models import PriceData # Ensure PriceData is available

        new_prices_added_count = 0
        for date_str, daily_data in time_series.items():
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Check if data for this stock_id and date already exists
            existing_price_data = db_session.query(PriceData).filter_by(stock_id=stock_id, date=date_obj).first()
            if existing_price_data:
                # print(f"  Price data for {stock_ticker} on {date_str} already exists. Skipping.")
                continue # Skip if already present

            try:
                new_price = PriceData(
                    stock_id=stock_id,
                    date=date_obj,
                    open=Decimal(daily_data["1. open"]),
                    high=Decimal(daily_data["2. high"]),
                    low=Decimal(daily_data["3. low"]),
                    close=Decimal(daily_data["4. close"]),
                    volume=int(daily_data["5. volume"])
                )
                db_session.add(new_price)
                new_prices_added_count += 1
            except KeyError as e:
                print(f"  Missing key {e} in daily data for {stock_ticker} on {date_str}. Data: {daily_data}")
                continue # Skip this entry
            except ValueError as e:
                print(f"  Error converting data for {stock_ticker} on {date_str}: {e}. Data: {daily_data}")
                continue # Skip this entry

        if new_prices_added_count > 0:
            print(f"  Added {new_prices_added_count} new daily price entries for {stock_ticker}.")
        else:
            print(f"  No new price data to add for {stock_ticker} (all up-to-date or no data).")
        
        # Commit after processing all daily data for this stock
        db_session.commit() 
        print(f"  Successfully processed and stored historical prices for {stock_ticker}.")
        return True

    except requests.exceptions.RequestException as e:
        print(f"  Request error fetching historical prices for {stock_ticker}: {e}")
        db_session.rollback()
        return False
    except Exception as e:
        print(f"  An unexpected error occurred processing historical prices for {stock_ticker}: {e}")
        db_session.rollback()
        return False


def populate_all_historical_prices(db_session: Session, api_key: str):
    """
    Iterates through all stocks in the DB and populates their historical price data.
    """
    print("\nStarting to populate historical prices for all stocks...")
    stocks = db_session.query(Stock).all()

    if not stocks:
        print("No stocks found in the database to populate historical prices for.")
        return

    for i, stock_item in enumerate(stocks):
        print(f"Processing historical data for: {stock_item.ticker} (ID: {stock_item.id})")
        
        success = fetch_and_store_historical_prices(db_session, api_key, stock_item.ticker, stock_item.id)
        
        if not success:
            # If fetch_and_store_historical_prices returned False, it means a rate limit or critical API error occurred.
            # It's safer to stop further API calls.
            print(f"  Stopping historical price population due to API issues with {stock_item.ticker}.")
            break 

        # Respect API rate limits, especially after a full data pull for one stock
        # No sleep after the last stock in the list
        if i < len(stocks) - 1:
            print(f"  Waiting 15 seconds before fetching next stock's historical data ({stock_item.ticker} done)...")
            time.sleep(15) # 15 seconds delay

    print("Finished populating historical prices for all stocks.")


def calculate_sma(price_data_list, window_period: int):
    """
    Calculates the Simple Moving Average (SMA) for a list of price data.

    Args:
        price_data_list: A list of objects or dictionaries, sorted by date ascending.
                         Each item must have a 'date' attribute/key (datetime.date object)
                         and a 'close' attribute/key (Decimal or float).
        window_period: The number of periods to use for the SMA calculation.

    Returns:
        A dictionary where keys are dates (datetime.date objects) and values
        are the calculated SMA (as float), or None if SMA cannot be calculated.
    """
    if not price_data_list or len(price_data_list) < window_period:
        return {}

    sma_results = {}
    
    # Ensure 'close' prices are numeric (Decimal or float).
    # The 'date' attribute is assumed to be a datetime.date object.

    # Iterate starting from the first point where an SMA can be calculated
    for i in range(window_period - 1, len(price_data_list)):
        # Slice the window_period of data points ending at the current point i
        window = price_data_list[i - window_period + 1 : i + 1]
        
        # Extract closing prices
        closing_prices = []
        valid_window = True
        for data_point in window:
            price = None
            if hasattr(data_point, 'close'): # For PriceData model instances
                price = data_point.close
            elif isinstance(data_point, dict) and 'close' in data_point: # For dictionaries
                price = data_point['close']
            
            if price is not None:
                try:
                    closing_prices.append(float(price)) # Convert to float for calculation
                except (ValueError, TypeError):
                    valid_window = False
                    break # Invalid price encountered
            else:
                valid_window = False # Missing 'close' price
                break
        
        current_date = getattr(price_data_list[i], 'date', price_data_list[i].get('date'))
        if not current_date: # Should ideally not happen if input is clean
            continue

        if valid_window and len(closing_prices) == window_period:
            current_sma = sum(closing_prices) / window_period
            sma_results[current_date] = round(current_sma, 2)
        # If window was not valid or not enough prices, SMA for current_date is not calculated,
        # so it's not added to sma_results, fulfilling the "Dates for which SMA cannot be calculated
        # should not be in the dictionary" requirement.

    return sma_results
