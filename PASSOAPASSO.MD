Criar adm master:

Config.py:
import pymysql

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='sua_senha',
        db='cadastro_tueEu',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

utils.py:
import bcrypt

    def hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

Função para criar administrador master:
from flask import Flask, request, jsonify
from config import get_connection
from utils import hash_senha

app = Flask(__name__)

@admin.route('/criar_admin_master', methods=['POST'])
def criar_admin_master():
    dados = request.get_json()

    nome = dados.get('nome')
    sexo = dados.get('sexo')
    cpf = dados.get('cpf')
    data_nasc = dados.get('data_nasc')
    telefone = dados.get('telefone')
    pais = dados.get('pais')
    estado = dados.get('estado')
    cidade = dados.get('cidade')
    cep = dados.get('cep')
    email = dados.get('email')
    senha = hash_senha(dados.get('senha'))

    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # Verifica se já existe um admin master
            cursor.execute("SELECT * FROM administrador WHERE is_master = 1")
            if cursor.fetchone():
                return jsonify({"erro": "Já existe um administrador master."}), 400

            # Cria usuário
            sql_usuario = """
                INSERT INTO usuario (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, cep, email, senha, email_verificado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """
            cursor.execute(sql_usuario, (
                nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, cep, email, senha
            ))
            usuario_id = connection.insert_id()

            # Cria administrador master
            sql_admin = "INSERT INTO administrador (usuario_id, is_master) VALUES (%s, 1)"
            cursor.execute(sql_admin, (usuario_id,))

            # Loga ação
            sql_log = """
                INSERT INTO logs (usuario_id, entidade, entidade_id, acao, detalhes)
                VALUES (%s, 'administrador', %s, 'criado', 'Administrador master criado')
            """
            cursor.execute(sql_log, (usuario_id, usuario_id))

            connection.commit()
        return jsonify({"mensagem": "Administrador master criado com sucesso."}), 201

    except Exception as e:
        print("Erro:", e)
        return jsonify({"erro": "Erro ao criar administrador master."}), 500


Excutar no console do sistema:
fetch('http://127.0.0.1:5000/admin/criar_admin_master', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    nome: 'Administardor Master', 
    sexo: 'Feminino',
    cpf: '12345678900',
    data_nasc: '1990-01-01',
    telefone: '61999999999',
    pais: 'Brasil',
    estado: 'DF',
    cidade: 'Brasília',
    cep: '70000000',
    email: 'master@tueeu.com.br', 
    senha: '1234' 
  })
})
.then(res => res.json())
.then(console.log)
.catch(console.error);

