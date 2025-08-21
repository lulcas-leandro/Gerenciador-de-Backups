from flask import Flask
from config import Config
import os

def criar_app(config_class=Config):
    app = Flask(__name__, static_folder='static')

    app.config.from_object(config_class)

    from app import routes
    app.register_blueprint(routes.routes_bp)

    return app

