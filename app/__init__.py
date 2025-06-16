# app/__init__.py
from flask import Flask
from config import Config
from dotenv import load_dotenv
load_dotenv()

def criar_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Registro dos blueprints
    # Supondo que você tenha os arquivos de rotas organizados em app/routes/
    from app.routes.auth import auth as auth_bp
    from app.routes.servicos import servicos as servicos_bp
    from app.routes.admin import admin as admin_bp
    from app.routes.main import main as main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(servicos_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
   


    return app
