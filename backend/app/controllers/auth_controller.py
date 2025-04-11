from flask import redirect, url_for, session, jsonify, request
from flask_dance.contrib.github import github
from ..utils.jwt_utils import create_jwt, decode_jwt


def github_login():
    if github.authorized:
        return redirect(url_for("auth.github_callback"))
    return redirect(url_for("github.login"))


def github_callback():
    if not github.authorized:
        return redirect(url_for("auth.github_login"))

    resp = github.get("/user")
    if not resp.ok:
        return "GitHub authentication failed!", 400

    user_data = resp.json()
    access_token = github.token["access_token"]

    user_info = {
        "username": user_data.get("login"),
        "avatar_url": user_data.get("avatar_url")
    }

    token = create_jwt(user_info, access_token)

    return redirect(f"http://localhost:3000/?token={token}")


def get_user():
    """API endpoint for frontend to get logged-in user details."""
    if "user_info" in session:
        return jsonify(session["user_info"])
    return jsonify({"error": "Not logged in"}), 401


def status():
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"user": None, "message": "Missing or invalid Authorization header"}), 401

    token = auth_header.split(" ")[1]
    user_data = decode_jwt(token)

    if not user_data:
        return jsonify({"user": None, "message": "Invalid or expired token"}), 401

    return jsonify({"user": user_data}), 200


def logout():
    session.pop("user_info", None)
    return redirect("http://localhost:3000")
