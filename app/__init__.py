from flask import Flask, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from app.db import db
from app.cache import cache
from app.routes import portfolio_bp, security_bp, trade_bp, user_bp


def create_app(config):
    try:
        app = Flask(__name__)
        app.config.from_object(config)

        # register extensions
        db.init_app(app)
        cache.init_app(app)

        # register blueprints
        app.register_blueprint(user_bp, url_prefix='/users')
        app.register_blueprint(portfolio_bp, url_prefix='/portfolios')
        app.register_blueprint(security_bp, url_prefix='/securities')
        app.register_blueprint(trade_bp, url_prefix='/trades')

        # Register error handlers
        @app.errorhandler(HTTPException)
        def handle_http_exception(e):
            return jsonify({'error': e.name, 'detail': e.description}), e.code

        @app.errorhandler(Exception)
        def handle_exception(e):
            db.session.rollback()
            detail = str(e) if app.debug else 'An unexpected error occurred'
            return jsonify({'error': 'Internal Server Error', 'detail': detail}), 500

        @app.errorhandler(ValidationError)
        def handle_validation_error(e: ValidationError):
            return jsonify({'error': 'Validation Error', 'detail': e.errors()}), 422

        return app
    except Exception as e:
        print(f'Error creating app: {e}')
        raise
