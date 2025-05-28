from flask import Blueprint, jsonify, abort
from ..models import Stock, PriceData, FundamentalData
from ..services.b3_data_service import calculate_sma # Import for SMA calculation
from .. import db # For potential direct session usage if needed, though usually through models

bp = Blueprint('stocks_api', __name__)

def serialize_datetime(dt_obj):
    """Helper to serialize datetime objects to ISO 8601 string."""
    if dt_obj:
        return dt_obj.isoformat()
    return None

def serialize_date(date_obj):
    """Helper to serialize date objects to YYYY-MM-DD string."""
    if date_obj:
        return date_obj.isoformat()
    return None

def serialize_decimal(decimal_obj):
    """Helper to serialize Decimal objects to string (or float if preferred)."""
    if decimal_obj is not None:
        return str(decimal_obj) # Using string representation for precision
    return None

@bp.route('/stocks', methods=['GET'])
def get_stocks():
    stocks = Stock.query.all()
    stocks_data = []
    for stock in stocks:
        stocks_data.append({
            "id": str(stock.id), # UUIDs are often better as strings in JSON
            "ticker": stock.ticker,
            "name": stock.name,
            "sector": stock.sector,
            "industry": stock.industry
        })
    return jsonify(stocks_data)

@bp.route('/stocks/<string:ticker>/history', methods=['GET'])
def get_stock_history(ticker):
    stock = Stock.query.filter_by(ticker=ticker).first()
    if not stock:
        abort(404, description=f"Stock with ticker {ticker} not found.")

    # Order by date descending for the final API output
    price_history_desc = PriceData.query.filter_by(stock_id=stock.id).order_by(PriceData.date.desc()).all()

    if not price_history_desc:
        return jsonify([])

    # For SMA calculation, data needs to be sorted ascending by date
    # Create a sorted list from the fetched data for SMA calculation
    price_history_asc = sorted(price_history_desc, key=lambda x: x.date)

    sma_20_values = calculate_sma(price_history_asc, 20)
    sma_50_values = calculate_sma(price_history_asc, 50)
    
    history_data = []
    # Iterate over the descending data for the response
    for price_entry in price_history_desc:
        current_date = price_entry.date # This is a datetime.date object
        history_data.append({
            "date": serialize_date(current_date),
            "open": serialize_decimal(price_entry.open),
            "high": serialize_decimal(price_entry.high),
            "low": serialize_decimal(price_entry.low),
            "close": serialize_decimal(price_entry.close),
            "volume": price_entry.volume, # Integer, directly serializable
            "sma_20": sma_20_values.get(current_date), # .get() returns None if key is missing
            "sma_50": sma_50_values.get(current_date)
        })
    return jsonify(history_data)

@bp.route('/stocks/<string:ticker>/fundamentals', methods=['GET'])
def get_stock_fundamentals(ticker):
    stock = Stock.query.filter_by(ticker=ticker).first()
    if not stock:
        abort(404, description=f"Stock with ticker {ticker} not found.")

    fundamental_data = FundamentalData.query.filter_by(stock_id=stock.id).first()
    if not fundamental_data:
        # As per instruction, return 404 or empty JSON. 404 seems more appropriate if fundamentals are expected.
        # Alternatively, could return jsonify({})
        abort(404, description=f"Fundamental data not found for stock {ticker}.")

    fundamentals_json = {
        "id": str(fundamental_data.id),
        "stock_id": str(fundamental_data.stock_id),
        "market_cap": serialize_decimal(fundamental_data.market_cap),
        "pe_ratio": serialize_decimal(fundamental_data.pe_ratio),
        "pb_ratio": serialize_decimal(fundamental_data.pb_ratio),
        "dividend_yield": serialize_decimal(fundamental_data.dividend_yield),
        "eps": serialize_decimal(fundamental_data.eps),
        "roe": serialize_decimal(fundamental_data.roe),
        "last_updated": serialize_datetime(fundamental_data.last_updated)
    }
    return jsonify(fundamentals_json)
