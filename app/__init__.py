from flask import Flask
from config import Config

def criar_app(config_class=Config):
    app = Flask(__name__, static_folder='static')

    app.config.from_object(config_class)

    from app import routes
    app.register_blueprint(routes.routes_bp)

    from app import agendador
    agendador.iniciar_agendador()

    return app

