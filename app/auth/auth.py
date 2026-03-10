from functools import wraps
import json
import logging
from flask import request, jsonify, g, current_app
import jwt
from jwt.algorithms import RSAAlgorithm
import requests

from app.cache import cache

logger = logging.getLogger(__name__)

class AuthError(Exception):
    def __init__(self, error: str, status_code: int):
        self.error = error
        self.status_code = status_code

def get_cognito_jwks_url() -> str:
    region = current_app.config.get("COGNITO_REGION")
    user_pool_id = current_app.config.get("COGNITO_USER_POOL_ID")
    return f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"

@cache.memoize(timeout=86400)
def get_jwks() -> dict:
    url = get_cognito_jwks_url()
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise AuthError("Unable to fetch JWKS for authentication.", 500)

def require_auth(f):
    """Determines if the Access Token is valid"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header:
            return jsonify({"error": "Authorization header is expected"}), 401
        
        parts = auth_header.split()
        if parts[0].lower() != "bearer":
            return jsonify({"error": "Authorization header must start with Bearer"}), 401
        elif len(parts) == 1:
            return jsonify({"error": "Token not found"}), 401
        elif len(parts) > 2:
            return jsonify({"error": "Authorization header must be Bearer token"}), 401
        
        token = parts[1]
        
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.PyJWTError:
            return jsonify({"error": "Invalid token header"}), 401
            
        rsa_key = {}
        jwks = get_jwks()
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header.get("kid"):
                rsa_key = RSAAlgorithm.from_jwk(json.dumps(key))
                break
                
        if not rsa_key:
            return jsonify({"error": "Unable to find appropriate key"}), 401
            
        try:
            client_id = current_app.config.get("COGNITO_APP_CLIENT_ID")
            region = current_app.config.get("COGNITO_REGION")
            user_pool_id = current_app.config.get("COGNITO_USER_POOL_ID")
            issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=client_id,
                issuer=issuer
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token is expired"}), 401
        except jwt.InvalidAudienceError:
            return jsonify({"error": "Incorrect claims, please check the audience"}), 401
        except Exception:
            return jsonify({"error": "Unable to parse authentication token."}), 401
            
        g.user_id = payload.get("sub")
        g.username = payload.get("username") or payload.get("cognito:username")
        g.current_user = payload
        
        return f(*args, **kwargs)

    return decorated
