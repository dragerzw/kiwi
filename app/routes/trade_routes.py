from flask import Blueprint, jsonify, request, g

from app.db import db
from app.schemas.trade_schemas import TradeBuyRequest, TradeSellRequest
from app.service import trade_service
from app.service.portfolio_service import has_portfolio_access
from app.auth import require_auth

trade_bp = Blueprint('trade', __name__)


@trade_bp.route('/buy', methods=['POST'])
@require_auth
def buy_trade():
    req_data = TradeBuyRequest(**(request.get_json(silent=True) or {}))
    if not has_portfolio_access(req_data.portfolio_id, g.username, ['Owner', 'Manager']):
        return jsonify({'error': 'Unauthorized to trade on this portfolio'}), 403
    trade_service.execute_purchase_order(
        portfolio_id=req_data.portfolio_id,
        ticker=req_data.ticker,
        quantity=req_data.quantity,
    )
    db.session.commit()
    return jsonify({'message': 'Purchase order executed successfully'}), 201


@trade_bp.route('/sell', methods=['POST'])
@require_auth
def sell_trade():
    req_data = TradeSellRequest(**(request.get_json(silent=True) or {}))
    if not has_portfolio_access(req_data.portfolio_id, g.username, ['Owner', 'Manager']):
        return jsonify({'error': 'Unauthorized to trade on this portfolio'}), 403
    trade_service.liquidate_investment(
        portfolio_id=req_data.portfolio_id,
        ticker=req_data.ticker,
        quantity=req_data.quantity,
        sale_price=req_data.sale_price,
    )
    db.session.commit()
    return jsonify({'message': 'Investment liquidated successfully'}), 200
