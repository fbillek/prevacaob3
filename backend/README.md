# B3 Stock Analysis - Backend

This backend server provides APIs for accessing and analyzing stock data from the B3 Brazilian Stock Exchange. It fetches data from Alpha Vantage, stores it in a PostgreSQL database, and exposes endpoints for stock information, historical prices (including SMAs), and fundamental data.

## Setup Instructions

1.  **Prerequisites:**
    *   Python 3.9+
    *   Pip
    *   Virtualenv (recommended)
    *   PostgreSQL server running

2.  **Clone the Repository (if applicable):**
    ```bash
    # git clone <repository_url>
    # cd <repository_name>/backend
    ```

3.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Environment Variables:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file with your specific configurations:
        *   `DATABASE_URL`: Your PostgreSQL connection string.
            *   Format: `postgresql://username:password@host:port/database_name`
        *   `FLASK_APP`: Should be set to `run.py` (or your main Flask app file).
        *   `FLASK_ENV`: Set to `development` for development mode.
        *   `ALPHA_VANTAGE_API_KEY`: Your API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key).

2.  **Database Initialization:**
    *   If this is the first time setting up the database with Alembic:
        ```bash
        flask db init  # Only if a 'migrations' folder doesn't exist
        ```
    *   Create the initial migration (if models have changed and no migration exists or if `flask db init` was just run):
        ```bash
        flask db migrate -m "Initial database setup"
        ```
    *   Apply migrations to create database tables:
        ```bash
        flask db upgrade
        ```

## Running the Application

1.  **Seed Initial Data:**
    *   To populate the database with a predefined list of B3 stocks and their historical price data, run the seeding command:
        ```bash
        flask seed-stocks
        ```
    *   This command uses the `ALPHA_VANTAGE_API_KEY` to fetch data. Ensure it is correctly set in your `.env` file. The free tier of Alpha Vantage has rate limits (e.g., 5 calls per minute), so the seeding process for historical data might take some time as it includes delays.

2.  **Run the Development Server:**
    ```bash
    flask run
    ```
    *   The server will typically start on `http://127.0.0.1:5000/`.

## API Endpoints

The following API endpoints are available:

*   **`GET /api/stocks`**
    *   Description: Retrieves a list of all available stocks stored in the database.
    *   Response: JSON array of stock objects, each including `id`, `ticker`, `name`, `sector`, `industry`.

*   **`GET /api/stocks/<ticker>/history`**
    *   Description: Retrieves historical daily price data (OHLCV) and calculated Simple Moving Averages (20-day and 50-day SMAs) for a specific stock ticker.
    *   `<ticker>`: The stock ticker symbol (e.g., `PETR4.SAO`).
    *   Response: JSON array of daily data objects, ordered by date (most recent first). Each object includes `date`, `open`, `high`, `low`, `close`, `volume`, `sma_20` (nullable), `sma_50` (nullable).

*   **`GET /api/stocks/<ticker>/fundamentals`**
    *   Description: Retrieves basic fundamental data for a specific stock ticker.
    *   `<ticker>`: The stock ticker symbol (e.g., `PETR4.SAO`).
    *   Response: JSON object containing fundamental data fields like `market_cap`, `pe_ratio`, `pb_ratio`, `dividend_yield`, etc. Returns 404 if no fundamental data is found for the stock.
