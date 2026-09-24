from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    from app.main import main_bp
    app.register_blueprint(main_bp)

    return app
