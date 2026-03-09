from flask import Blueprint, jsonify, request, g

import app.service.portfolio_service as portfolio_service
import app.service.transaction_service as transaction_service
import app.service.user_service as user_service
from app.db import db
from app.schemas.portfolio_schemas import PortfolioCreateRequest
from app.schemas.portfolio_access_schemas import PortfolioAccessRequest
from app.service.alpha_vantage_client import get_quote
from app.auth import require_auth

portfolio_bp = Blueprint('portfolio', __name__)

def _enrich_portfolio(portfolio_dict: dict) -> dict:
    total_value = 0.0
    for inv in portfolio_dict.get('investments', []):
        quote = get_quote(inv['ticker'])
        if quote:
            inv['current_price'] = quote.price
            inv['total_value'] = quote.price * inv['quantity']
            total_value += inv['total_value']
        else:
            inv['current_price'] = 0.0
            inv['total_value'] = 0.0
    
    portfolio_dict['total_portfolio_value'] = total_value
    return portfolio_dict

@portfolio_bp.route('/', methods=['GET'])
@require_auth
def get_all_portfolios():
    portfolios = portfolio_service.get_all_portfolios()
    return jsonify([_enrich_portfolio(p.__to_dict__()) for p in portfolios]), 200


@portfolio_bp.route('/<int:portfolio_id>', methods=['GET'])
@require_auth
def get_portfolio(portfolio_id):
    if not portfolio_service.has_portfolio_access(portfolio_id, g.username, ['Owner', 'Manager', 'Viewer']):
        return jsonify({'error': 'Unauthorized to view this portfolio'}), 403
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id)
    if portfolio is None:
        return jsonify({'error': f'Portfolio {portfolio_id} not found'}), 404
    return jsonify(_enrich_portfolio(portfolio.__to_dict__())), 200


@portfolio_bp.route('/user/<username>', methods=['GET'])
@require_auth
def get_portfolios_by_user(username):
    user = user_service.get_user_by_username(username)
    if user is None:
        return jsonify({'error': f'User {username} not found'}), 404
    portfolios = portfolio_service.get_portfolios_by_user(user)
    return jsonify([_enrich_portfolio(p.__to_dict__()) for p in portfolios]), 200


@portfolio_bp.route('/', methods=['POST'])
@require_auth
def create_portfolio():
    req_data = PortfolioCreateRequest(**request.get_json())
    if g.username != req_data.username:
        return jsonify({'error': 'Can only create portfolio for authenticated user'}), 403
    user = user_service.get_user_by_username(req_data.username)
    if user is None:
        return jsonify({'error': f'User {req_data.username} not found'}), 404
    portfolio_id = portfolio_service.create_portfolio(
        name=req_data.name,
        description=req_data.description,
        user=user,
    )
    db.session.commit()
    return jsonify({'message': 'Portfolio created successfully', 'portfolio_id': portfolio_id}), 201


@portfolio_bp.route('/<int:portfolio_id>', methods=['DELETE'])
@require_auth
def delete_portfolio(portfolio_id):
    if not portfolio_service.has_portfolio_access(portfolio_id, g.username, ['Owner']):
        return jsonify({'error': 'Only the Owner can delete this portfolio'}), 403
    portfolio_service.delete_portfolio(portfolio_id)
    db.session.commit()
    return jsonify({'message': 'Portfolio deleted successfully'}), 200


@portfolio_bp.route('/<int:portfolio_id>/transactions', methods=['GET'])
@require_auth
def get_portfolio_transactions(portfolio_id):
    if not portfolio_service.has_portfolio_access(portfolio_id, g.username, ['Owner', 'Manager', 'Viewer']):
        return jsonify({'error': 'Unauthorized to view this portfolio info'}), 403
    transactions = transaction_service.get_transactions_by_portfolio_id(portfolio_id)
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200

@portfolio_bp.route('/<int:portfolio_id>/access', methods=['POST'])
@require_auth
def grant_access(portfolio_id):
    if not portfolio_service.has_portfolio_access(portfolio_id, g.username, ['Owner']):
        return jsonify({'error': 'Only the Owner can grant access to this portfolio'}), 403
    req_data = PortfolioAccessRequest(**request.get_json())
    portfolio_service.grant_portfolio_access(portfolio_id, req_data.username, req_data.role)
    db.session.commit()
    return jsonify({'message': 'Portfolio access granted successfully'}), 200

@portfolio_bp.route('/<int:portfolio_id>/access/<username>', methods=['DELETE'])
@require_auth
def revoke_access(portfolio_id, username):
    if not portfolio_service.has_portfolio_access(portfolio_id, g.username, ['Owner']):
        return jsonify({'error': 'Only the Owner can revoke access to this portfolio'}), 403
    portfolio_service.revoke_portfolio_access(portfolio_id, username)
    db.session.commit()
    return jsonify({'message': 'Portfolio access revoked successfully'}), 200
