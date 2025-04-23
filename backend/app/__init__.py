from flask import Flask, redirect
from flask_cors import CORS
from flask_dance.contrib.github import make_github_blueprint
from .config import Config


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)

    github_bp = make_github_blueprint(
        client_id=app.config["GITHUB_CLIENT_ID"],
        client_secret=app.config["GITHUB_CLIENT_SECRET"],
        scope="read:user,repo",
        redirect_to="auth.github_callback",
    )
    app.register_blueprint(github_bp, url_prefix="/auth")
    from .routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth/routes")
    from .routes.report_routes import report_bp
    app.register_blueprint(report_bp, url_prefix="/report")
    from .routes.file_routes import file_bp
    app.register_blueprint(file_bp, url_prefix="/pdf")
    return app
