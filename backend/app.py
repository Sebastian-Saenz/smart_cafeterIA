from flask import Flask, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from config import Config
from extensions import db, jwt, pool, test_PostgreSQL, test_Elasticsearch, test_Pool
import os
from routes.client import client_bp
from routes.auth import auth_bp
from flask_jwt_extended import JWTManager


def create_app():
    # Permitir OAuth en HTTP local (solo desarrollo)
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static",
    )
    app.secret_key = app.config["SECRET_KEY"] 
    jwt = JWTManager(app)
    app.config.from_object(Config)

    app.config.update(
        {
            "CLIENT_SECRETS_FILE": os.path.join("backend", "client_secret.json"),  # JSON descargado de GCP
            "SCOPES": [
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
            "REDIRECT_URI": "https://8080-cs-6d82139e-bba8-403a-8cef-00afd4e3f4ac.cs-us-east1-pkhd.cloudshell.dev/auth/callback",
        }
    )

    # 3. Registrar blueprints
    app.register_blueprint(client_bp, url_prefix="/client")
    app.register_blueprint(auth_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    # Context processor para inyectar user en templates
    @app.context_processor
    def inject_user():
        user=session.get("user")
        email = user.get("email")
        return dict(user=user, user_email=email)

    return app


if __name__ == "__main__":
    app = create_app()
    config = Config()
    test_PostgreSQL()
    test_Elasticsearch()
    test_Pool()
    app.run(host="0.0.0.0", port=8080)
