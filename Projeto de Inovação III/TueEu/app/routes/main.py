# Exemplo: app/routes/main.py
from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
def pagina_inicial():
    return render_template('index.html')

@main.route('/cadastro')
def mostrar_cadastro():
    return render_template('cadastro.html')
