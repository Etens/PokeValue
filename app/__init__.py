from flask import Flask
from app.backend.routes import backend_routes
from app.backend.models import init_db


def create_app():
    app = Flask(__name__)

    init_db()

    app.register_blueprint(backend_routes)

    return app
