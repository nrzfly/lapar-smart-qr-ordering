import os
from flask import Flask

from .db import init_db


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "lapar-smart-dev-secret")
    app.config["ADMIN_PASSCODE"] = os.environ.get("ADMIN_PASSCODE", "admin123")

    with app.app_context():
        init_db()

    from .routes_staff import staff_bp
    from .routes_admin import admin_bp

    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)

    return app
