from functools import wraps
from flask import request, jsonify
from ..utils.jwt_utils import decode_jwt


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]
        user = decode_jwt(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.user = user
        return f(*args, **kwargs)
    return decorated
