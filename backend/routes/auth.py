from flask import Blueprint, request, current_app, jsonify, render_template, session, redirect, url_for
from google_auth_oauthlib.flow import Flow
import google.oauth2.credentials
import googleapiclient.discovery

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/google", methods=["POST"])
def google_auth():
    data = request.get_json()
    code = data.get("code")
    if not code:
        return jsonify({"error": "No code"}), 400

    flow = Flow.from_client_secrets_file(
        current_app.config["CLIENT_SECRETS_FILE"],
        scopes=current_app.config["SCOPES"],
        redirect_uri=current_app.config["REDIRECT_URI"],
    )
    flow.fetch_token(code=code)

    creds = flow.credentials
    # Construimos el servicio OAuth2 y pedimos el perfil
    oauth2 = googleapiclient.discovery.build("oauth2", "v2", credentials=creds)
    info = oauth2.userinfo().get().execute()

    # Guardamos credenciales y user-info en sesión
    session["credentials"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    session["user"] = {
        "email": info.get("email"),
        "name": info.get("name"),
        "picture": info.get("picture"),
    }

    return jsonify({
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "expires_in": creds.expiry.timestamp(),
        "user": session["user"]
    })

@auth_bp.route("/callback")
def callback():
    return render_template("callback.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
