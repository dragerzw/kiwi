import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    CACHE_TYPE = 'SimpleCache'
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
    COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
    COGNITO_APP_CLIENT_ID = os.environ.get('COGNITO_APP_CLIENT_ID')
    COGNITO_REGION = os.environ.get('COGNITO_REGION', 'us-east-1')


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    ALPHA_VANTAGE_API_KEY = 'test_key'
    COGNITO_USER_POOL_ID = 'test_pool'
    COGNITO_APP_CLIENT_ID = 'test_client'
    COGNITO_REGION = 'us-east-1'


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL', 'sqlite+pysqlite:///dev.db')
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        f'mysql+pymysql://{os.environ.get("DB_USER", "")}:'
        f'{os.environ.get("DB_PASSWORD", "")}@'
        f'{os.environ.get("DB_HOST", "")}:'
        f'{os.environ.get("DB_PORT", "3306")}/'
        f'{os.environ.get("DB_NAME", "")}'
    )
    DEBUG = False
    SQLALCHEMY_ECHO = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestConfig,
}


def get_config(env: str):
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)
