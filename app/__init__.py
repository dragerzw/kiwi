from flask import Flask, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from app.db import db
from app.cache import cache
from app.routes import portfolio_bp, security_bp, trade_bp, user_bp
from app.schemas.error_schemas import ErrorResponse


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
            code = getattr(e, 'code', 500)
            error_response = ErrorResponse(error=e.description or e.name, code=code)
            return jsonify(error_response.model_dump()), code

        @app.errorhandler(ValidationError)
        def handle_validation_error(error: ValidationError):
            first_error = error.errors()[0]
            error_message = f"{first_error['loc'][0]}: {first_error['msg']}"
            error_response = ErrorResponse(error=error_message, code=400)
            return jsonify(error_response.model_dump()), 400

        @app.errorhandler(404)
        def handle_not_found(error):
            error_response = ErrorResponse(error="Resource not found", code=404)
            return jsonify(error_response.model_dump()), 404

        # Domain exception handlers
        from app.service.user_service import UnsupportedUserOperationError
        from app.service.portfolio_service import UnsupportedPortfolioOperationError
        from app.service.trade_service import TradeExecutionException, InsufficientFundsError

        @app.errorhandler(UnsupportedUserOperationError)
        def handle_user_error(e):
            error_response = ErrorResponse(error=str(e), code=400)
            return jsonify(error_response.model_dump()), 400

        @app.errorhandler(UnsupportedPortfolioOperationError)
        def handle_portfolio_error(e):
            error_response = ErrorResponse(error=str(e), code=400)
            return jsonify(error_response.model_dump()), 400

        @app.errorhandler(TradeExecutionException)
        def handle_trade_error(e):
            error_response = ErrorResponse(error=str(e), code=400)
            return jsonify(error_response.model_dump()), 400

        @app.errorhandler(InsufficientFundsError)
        def handle_insufficient_funds_error(e):
            error_response = ErrorResponse(error=str(e), code=400)
            return jsonify(error_response.model_dump()), 400

        @app.errorhandler(Exception)
        def handle_exception(e):
            db.session.rollback()
            detail = str(e) if app.debug else 'An unexpected error occurred'
            error_response = ErrorResponse(error=detail, code=500)
            return jsonify(error_response.model_dump()), 500

        return app
    except Exception as e:
        print(f'Error creating app: {e}')
        raise
