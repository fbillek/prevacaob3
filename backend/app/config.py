import os

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Other global configurations

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://user:password@host:port/dbname')
    # Other development specific configs

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:') # Use in-memory SQLite for tests
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Any other test-specific configs, e.g., disable CSRF, set different API keys if needed
    ALPHA_VANTAGE_API_KEY = 'test_api_key_for_pytest' # Ensure tests don't hit real API

# You might want to add a ProductionConfig as well
# class ProductionConfig(Config):
#     DEBUG = False
#     SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
#     # etc.

# Function to load config based on environment variable or default
def get_config():
    env = os.getenv('FLASK_ENV', 'development').lower()
    if env == 'testing':
        return TestingConfig
    # elif env == 'production':
    #     return ProductionConfig
    return DevelopmentConfig
