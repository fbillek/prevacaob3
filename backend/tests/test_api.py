import pytest
import json

def test_get_stocks_empty_db(client):
    """
    Test the /api/stocks endpoint when the database is empty.
    """
    response = client.get('/api/stocks')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_history_non_existent_ticker(client):
    """
    Test the /api/stocks/<ticker>/history endpoint for a non-existent ticker.
    """
    response = client.get('/api/stocks/NONEXISTENTTICKER/history')
    assert response.status_code == 404
    assert response.is_json
    data = response.get_json()
    assert "description" in data
    assert "Stock with ticker NONEXISTENTTICKER not found." in data["description"]


def test_get_fundamentals_non_existent_ticker(client):
    """
    Test the /api/stocks/<ticker>/fundamentals endpoint for a non-existent ticker.
    """
    response = client.get('/api/stocks/NONEXISTENTTICKER/fundamentals')
    assert response.status_code == 404
    assert response.is_json
    data = response.get_json()
    assert "description" in data
    assert "Stock with ticker NONEXISTENTTICKER not found." in data["description"]

# Optional: Example of testing with some data (requires db fixture and model imports)
# from app.models import Stock
# def test_get_stocks_with_data(client, db):
#     """
#     Test the /api/stocks endpoint when there is data.
#     """
#     # Add some test data
#     stock1 = Stock(ticker="TEST1.SAO", name="Test Stock 1", sector="Test Sector", industry="Test Industry")
#     stock2 = Stock(ticker="TEST2.SAO", name="Test Stock 2", sector="Test Sector", industry="Test Industry")
#     db.session.add_all([stock1, stock2])
#     db.session.commit()

#     response = client.get('/api/stocks')
#     assert response.status_code == 200
#     assert response.is_json
#     data = response.get_json()
#     assert isinstance(data, list)
#     assert len(data) == 2
#     assert data[0]['ticker'] == "TEST1.SAO"
#     assert data[1]['ticker'] == "TEST2.SAO"

    # Clean up: The db fixture in conftest.py (if session-scoped for app context) 
    # and its teardown (drop_all) will handle cleanup for in-memory DB.
    # If you had function-scoped db changes you wanted to revert, you might do:
    # db.session.delete(stock1)
    # db.session.delete(stock2)
    # db.session.commit()
    # However, for in-memory, letting the app fixture handle create/drop is cleanest.

# Note: Tests for /history and /fundamentals with *existing* data would require
# more complex data setup (Stock, PriceData, FundamentalData instances) and 
# potentially mocking of the calculate_sma function if its dependencies are complex
# or if you want to isolate the API logic.
# For this subtask, only non-existent ticker tests are required for those endpoints.
