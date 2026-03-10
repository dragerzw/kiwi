from flask import Blueprint, jsonify, g

import app.service.security_service as security_service
import app.service.transaction_service as transaction_service

from dataclasses import asdict
from app.auth import require_auth
from app.service.security_service import SecurityNotFoundException, SecurityFetchException
from app.schemas.error_schemas import ErrorResponse


security_bp = Blueprint('security', __name__)

@security_bp.route('/', methods=['GET'])
@require_auth
def get_all_securities():
    securities = security_service.get_all_securities()
    return jsonify([asdict(security) for security in securities]), 200


@security_bp.route('/<ticker>', methods=['GET'])
@require_auth
def get_security(ticker):
    try:
        security = security_service.get_security_by_ticker(ticker)
        return jsonify(asdict(security)), 200
    except SecurityNotFoundException as e:
        error_response = ErrorResponse(error=str(e), code=404)
        return jsonify(error_response.model_dump()), 404
    except SecurityFetchException as e:
        error_response = ErrorResponse(error=str(e), code=502)
        return jsonify(error_response.model_dump()), 502


@security_bp.route('/<ticker>/transactions', methods=['GET'])
@require_auth
def get_security_transactions(ticker):
    transactions = transaction_service.get_transactions_by_ticker(ticker)
    sanitized_transactions = []
    for transaction in transactions:
        transaction_dict = transaction.__to_dict__()
        transaction_dict.pop('username', None)
        transaction_dict.pop('portfolio_id', None)
        sanitized_transactions.append(transaction_dict)
    return jsonify(sanitized_transactions), 200
