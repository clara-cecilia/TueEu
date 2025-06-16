import os
from dotenv import load_dotenv

load_dotenv()  # Carrega as variáveis do .env

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Se quiser utilizar a variável de ambiente SECRET_KEY, caso não exista, usa o fallback
    SECRET_KEY = os.environ.get("SECRET_KEY", "chave_secreta_fallback")
    # Configuração de Upload Folder
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    # Configurações do banco de dados
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "2904")
    DB_PORT = os.environ.get("DB_PORT", 3306)
    DB_NAME = os.environ.get("DB_NAME", "cadastro_tueeu")
