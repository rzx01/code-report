from flask import Blueprint
from ..controllers.auth_controller import github_login, github_callback, logout, status

auth_bp = Blueprint("auth", __name__)

auth_bp.add_url_rule("/login", view_func=github_login)
auth_bp.add_url_rule("/github", view_func=github_callback)
auth_bp.add_url_rule("/logout", view_func=logout)
auth_bp.add_url_rule("/status", view_func=status)
