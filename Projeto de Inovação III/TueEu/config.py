import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "chave_secreta_fallback")
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "chave_secreta_fallback")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "280697")
    DB_PORT = os.environ.get("DB_PORT", 3306)
    DB_NAME = os.environ.get("DB_NAME", "cadastro_tueeu")
