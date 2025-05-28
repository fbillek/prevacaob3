from app import create_app, db
from app.models import Stock, PriceData, FundamentalData, NewsArticle
from app.services.b3_data_service import fetch_and_store_stock_details
from flask_migrate import Migrate
import click
import os

app = create_app()
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Stock=Stock, PriceData=PriceData, FundamentalData=FundamentalData, NewsArticle=NewsArticle)

@app.cli.command("seed-stocks")
def seed_stocks_command():
    """Fetches and stores predefined B3 stock details from Alpha Vantage."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        click.echo("Error: ALPHA_VANTAGE_API_KEY not set in environment.")
        return

    # Use a context for the database session
    with app.app_context():
        # db.session can be used here as it's managed by Flask-SQLAlchemy
        click.echo("Starting stock details seeding...")
        fetch_and_store_stock_details(db.session, api_key)
        click.echo("Stock details seeding completed.")
        
        click.echo("\nStarting historical price data population...")
        from app.services.b3_data_service import populate_all_historical_prices # Import here to ensure app context is active
        populate_all_historical_prices(db.session, api_key)
        click.echo("Historical price data population completed.")
        
        # Final commit, though individual services might commit more frequently.
        # db.session.commit() # Service functions handle their own commits.

        click.echo("\nAll seeding processes completed.")

if __name__ == '__main__':
    app.run()
