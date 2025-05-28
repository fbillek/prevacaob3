from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Load configuration from app.config using get_config
    # This will load TestingConfig if FLASK_ENV is 'testing' (set by pytest.ini)
    # or DevelopmentConfig otherwise (or based on .env for normal runs)
    app.config.from_object(get_config()) # Correctly get the config class

    db.init_app(app)
    migrate.init_app(app, db)

    # Register Blueprints here
    from .api.stocks_api import bp as stocks_api_bp
    app.register_blueprint(stocks_api_bp, url_prefix='/api')
    
    from .config import get_config # Import get_config

    return app
