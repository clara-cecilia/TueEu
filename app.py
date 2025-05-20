from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import bcrypt
from bcrypt import hashpw, gensalt, checkpw
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'chave_secreta'  # Necessária para usar sessões

# -------------------------- CONEXÃO COM BANCO --------------------------

def conectar_bd():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="2904",
            port='3306',
            database="cadastro_tueeu"
        )
        print("Conexão realizada com sucesso!")
        return db
    except mysql.connector.Error as err:
        print(f"Erro na conexão: {err}")
        return None

db = conectar_bd()

# -------------------------- FUNÇÕES DE RESET DE SENHA --------------------------

def generate_reset_code():
    return str(random.randint(100000, 999999))

def store_reset_code_in_db(email, code):
    cursor = db.cursor()
    cursor.execute("DELETE FROM reset_senhas WHERE email = %s", (email,))
    cursor.execute(
        "INSERT INTO reset_senhas (email, codigo, expiracao) VALUES (%s, %s, %s)",
        (email, code, datetime.now() + timedelta(minutes=10))
    )
    db.commit()
    cursor.close()

def send_reset_email(email, code):
    remetente = "seuemail@gmail.com"
    senha_email = "sua_senha"

    msg = MIMEText(f"Seu código de recuperação é: {code}")
    msg["Subject"] = "Recuperação de senha"
    msg["From"] = remetente
    msg["To"] = email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(remetente, senha_email)
            servidor.send_message(msg)
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

def verify_reset_code(email, code):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reset_senhas WHERE email = %s AND codigo = %s", (email, code))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado and resultado["expiracao"] > datetime.now()

def reset_password(email, nova_senha):
    nova_senha_hash = hashpw(nova_senha.encode('utf-8'), gensalt()).decode('utf-8')
    cursor = db.cursor()
    cursor.execute("UPDATE usuario SET senha = %s WHERE email = %s", (nova_senha_hash, email))
    db.commit()
    cursor.execute("DELETE FROM reset_senhas WHERE email = %s", (email,))
    db.commit()
    cursor.close()

# -------------------------- ROTAS BÁSICAS --------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

@app.route('/esqueceu-senha')
def esqueceuSenha():
    return render_template('esqueceuSenha.html')

@app.route('/home')
def home():
    if 'usuario' in session:
        return render_template('home.html', usuario=session['usuario'])
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Você saiu do sistema.')
    return redirect(url_for('login'))

# -------------------------- CADASTRO --------------------------

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    cursor = db.cursor()
    
    email = request.form['email']   
    email_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
    senha_criptografada = hashpw(request.form['senha'].encode('utf-8'), gensalt())

    dados = (
        request.form['nome'], request.form['sexo'], request.form['cpf'],
        request.form['data_nasc'], request.form['telefone'], request.form['pais'],
        request.form['estado'], request.form['cidade'], request.form['bairro'],
        request.form['cep'], request.form['endereco'], email_hash, senha_criptografada
    )

    sql = """
    INSERT INTO usuario (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, bairro, cep, endereco, email, senha)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(sql, dados)
    db.commit()
    cursor.close()
    
    return redirect('home')

# -------------------------- LOGIN --------------------------

@app.route('/logar', methods=['POST'])
def logar():
    email = request.form['email']
    senha = request.form['senha']

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE email = %s", (email,))
    usuario = cursor.fetchone()
    cursor.close()

    if usuario:
        senha_armazenada = usuario['senha']
        
        if checkpw(senha.encode('utf-8'), senha_armazenada.encode('utf-8')):
            session['usuario'] = usuario['nome']
            session['is_admin'] = usuario.get('is_admin', 0)

            flash('Login realizado com sucesso!')
            return redirect(url_for('admin' if usuario['is_admin'] == 1 else 'home'))
        
        flash('Senha incorreta.')
    else:
        flash('E-mail não encontrado.')

    return redirect(url_for('login'))  # redireciona para login se falhar


# -------------------------- RECUPERAÇÃO DE SENHA --------------------------

@app.route('/recuperar-senha', methods=['POST'])
def recuperar_senha():
    data = request.get_json()
    email = data.get("email")
    reset_code = generate_reset_code()
    
    store_reset_code_in_db(email, reset_code)
    send_reset_email(email, reset_code)

    return jsonify({"message": "Código enviado para o e-mail."}), 200

@app.route("/redefinir-senha", methods=["POST"])
def redefinir_senha():
    data = request.get_json()
    email = data.get("email")
    codigo = data.get("reset_code")
    nova_senha = data.get("nova_senha")

    if verify_reset_code(email, codigo):
        reset_password(email, nova_senha)
        return jsonify({"message": "Senha redefinida com sucesso!"})
    
    return jsonify({"error": "Código inválido ou e-mail não encontrado."}), 400

# -------------------------- FUNÇOES ADM --------------------------
@app.route('/admin')
def admin():
    if 'usuario' not in session or not session.get('is_admin'):
        flash("Acesso restrito.")
        return redirect(url_for('login'))

    return render_template('admin.html')

@app.route('/gerenciarUsuarios')
def gerenciarUsuarios():
    if not session.get('is_admin'):
        flash("Acesso negado.")
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE is_admin = 0")
    usuarios = cursor.fetchall()
    cursor.close()

    return render_template('gerenciarUsuarios.html', usuarios=usuarios)

@app.route('/gerenciarAdms')
def gerenciarAdministradores():
    if not session.get('is_admin'):
        flash("Acesso negado.")
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE is_admin = 1")
    admins = cursor.fetchall()
    cursor.close()

    return render_template('gerenciarAdministradores.html', admins=admins)

@app.route('/novoAdmin', methods=['POST'])
def novoAdmin():
    try:
        nome = request.form['nome']
        sexo = request.form['sexo']
        data_nasc = request.form['data_nasc']
        pais = request.form['pais']
        estado = request.form['estado']
        cidade = request.form['cidade']
        bairro = request.form['bairro']
        email = request.form['email']
        senha = request.form['senha']

        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO usuario 
            (nome, sexo, data_nasc, pais, estado, cidade, bairro, email, senha, is_admin, is_master_admin) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 0)
        """, (nome, sexo, data_nasc, pais, estado, cidade, bairro, email, senha_hash))
        
        db.commit()
        cursor.close()

        flash("Administrador cadastrado com sucesso!", "sucesso")
    except Exception as e:
        flash("Erro ao cadastrar administrador: " + str(e), "erro")

    return redirect(url_for('gerenciarAdministradores'))

@app.route('/editarUsuario/<int:id>', methods=['GET', 'POST'])
def editarUsuario(id):
    if 'usuario' not in session or not session.get('is_admin'):
        flash("Acesso restrito.")
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE id = %s", (id,))
    usuario = cursor.fetchone()

    if not usuario:
        flash("Usuário não encontrado.")
        return redirect(url_for('admin'))

    if request.method == 'POST':
        nome = request.form['nome']
        sexo = request.form['sexo']
        cpf = request.form['cpf']
        data_nasc = request.form['data_nasc']
        telefone = request.form['telefone']
        pais = request.form['pais']
        estado = request.form['estado']
        cidade = request.form['cidade']
        bairro = request.form['bairro']
        cep = request.form['cep']
        endereco = request.form['endereco']
        email = request.form['email']
        senha = request.form['senha']

        if senha:
            cursor.execute("""
                UPDATE usuario SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                pais=%s, estado=%s, cidade=%s, bairro=%s, cep=%s, endereco=%s, email=%s, senha=SHA2(%s, 256)
                WHERE id=%s
            """, (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, bairro, cep, endereco, email, senha, id))
        else:
            cursor.execute("""
                UPDATE usuario SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                pais=%s, estado=%s, cidade=%s, bairro=%s, cep=%s, endereco=%s, email=%s
                WHERE id=%s
            """, (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, bairro, cep, endereco, email, id))
        
        db.commit()
        cursor.close()
        flash("Usuário atualizado com sucesso.")
        return redirect(url_for('admin'))

    cursor.close()
    return render_template('editarUsuario.html', usuario=usuario)

@app.route('/excluirUsuario/<int:id>', methods=['POST'])
def excluirUsuario(id):
    if 'usuario' not in session or not session.get('is_admin'):
        flash("Acesso restrito.")
        return redirect(url_for('login'))

    cursor = db.cursor()
    # Prevenir exclusão do admin master (exemplo: id=1)
    if id == 1:
        flash("Não é possível excluir o administrador master.")
        return redirect(url_for('admin'))

    cursor.execute("DELETE FROM usuario WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    flash("Usuário excluído com sucesso.")
    return redirect(url_for('admin'))



# -------------------------- RODAR APP --------------------------

if __name__ == '__main__':
    app.run(debug=True)
