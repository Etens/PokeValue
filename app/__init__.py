from flask import Flask
from app.backend.routes.add_card import add_card
from app.backend.routes.get_card_value import get_card_value
from app.backend.models import init_db


def create_app():
    app = Flask(__name__)

    init_db()

    app.register_blueprint(add_card)
    app.register_blueprint(get_card_value)

    return app
