import pytest
from app import create_app # From backend/app/__init__.py
from app.config import TestingConfig # From backend/app/config.py
from app import db as _db # Assuming db is in backend/app/__init__.py

@pytest.fixture(scope='session')
def app():
    """
    Session-wide test Flask application.
    Ensures the app is created with TestingConfig and handles context.
    """
    # Ensure FLASK_ENV is set to 'testing' for create_app to pick up TestingConfig
    # This should be handled by pytest.ini, but being explicit here can also help.
    # However, create_app in this project now directly uses get_config() which checks os.getenv('FLASK_ENV')
    
    flask_app = create_app() # Relies on FLASK_ENV=testing from pytest.ini to load TestingConfig

    with flask_app.app_context():
        # If using an in-memory SQLite, tables need to be created.
        # For other test DBs, this might be handled differently (e.g., Alembic migrations).
        if flask_app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:':
            _db.create_all()
        
        yield flask_app # Provide the app object to tests

        # Teardown: drop all tables if it was an in-memory SQLite DB
        if flask_app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:':
            _db.session.remove() # Ensure session is closed before dropping
            _db.drop_all()

@pytest.fixture(scope='function') # Changed to function scope for client and potentially DB state per test
def client(app):
    """
    A test client for the app.
    Function scope ensures a clean client for each test.
    """
    return app.test_client()

@pytest.fixture(scope='function')
def db(app):
    """
    Provides the database instance, ensuring it's within the app context.
    This can be used if tests need to directly interact with the DB session.
    """
    with app.app_context():
        yield _db
        # Optional: if you want to ensure no pending transactions between tests
        # _db.session.remove()
        # _db.session.rollback() # Or rollback to clean state if tests modify DB and don't commit
                                # For in-memory, drop_all in app fixture handles broader cleanup.
                                # For persistent DB, more sophisticated session handling might be needed.
                                # For this setup, app fixture's drop_all is the main cleanup.
