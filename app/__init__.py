from flask import Flask

from app.backend.models import init_db
from app.backend.routes.add_card import add_card_routes
from app.backend.routes.get_card_value import get_card_value_routes
from app.backend.routes.progress import progress


def create_app():
    app = Flask(__name__)

    init_db()

    app.register_blueprint(add_card_routes)
    app.register_blueprint(get_card_value_routes)
    app.register_blueprint(progress)

    return app
