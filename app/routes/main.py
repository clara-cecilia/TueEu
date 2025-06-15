# Exemplo: app/routes/main.py
from flask import Blueprint, render_template
from flask import Flask
from config import Config
from app.routes.servicos import servicos  # importe seu blueprint


app = Flask(__name__)
app.config.from_object(Config)  # Carrega as configurações do Config

# Registre o blueprint (certifique-se de que o caminho esteja correto)
app.register_blueprint(servicos)

if __name__ == '__main__':
    app.run(debug=True)
main = Blueprint('main', __name__)

@main.route('/')
def pagina_inicial():
    return render_template('index.html')

@main.route('/cadastro')
def mostrar_cadastro():
    return render_template('cadastro.html')
