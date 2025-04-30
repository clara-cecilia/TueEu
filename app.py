from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import bcrypt
from bcrypt import hashpw, gensalt, checkpw
import hashlib
from reset_utils import generate_reset_code, store_reset_code_in_db, send_reset_email, verify_reset_code, reset_password

app = Flask(__name__)
app.secret_key = 'chave_secreta'  # Necessária para usar sessões

# Conexão com banco de dados
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="280697",
        port='3306',
        database="cadastro_tueeu"
    )
    print("Conexão realizada com sucesso!")
except mysql.connector.Error as err:
    print(f"Erro na conexão: {err}")

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
    return redirect(url_for('login'))

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

    dados = (
        request.form['nome'],
        request.form['sexo'],
        request.form['cpf'],
        request.form['data_nasc'],
        request.form['telefone'],
        request.form['pais'],
        request.form['estado'],
        request.form['cidade'],
        request.form['bairro'],
        request.form['cep'],
        request.form['endereco'],
        email_hash,
        request.form['senha']
    )

    senha_criptografada = hashpw(dados[-1].encode('utf-8'), gensalt())
    dados = (*dados[:-1], senha_criptografada)

    sql = '''
    INSERT INTO usuario (
        nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade,
        bairro, cep, endereco, email, senha
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    cursor.execute(sql, dados)
    db.commit()
    cursor.close()
    return redirect('/')

# -------------------------- LOGIN --------------------------

@app.route('/logar', methods=['POST'])
def logar():
    email = request.form['email']
    senha = request.form['senha']

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE email = %s", (email,))
    usuario = cursor.fetchone()

    if usuario:
        senha_armazenada = usuario['senha']
        if checkpw(senha.encode('utf-8'), senha_armazenada.encode('utf-8')):
            session['usuario'] = usuario['nome']
            session['is_admin'] = usuario.get('is_admin', 0)
            if usuario['is_admin'] == 1:
                flash('Login realizado como administrador!')
                return redirect(url_for('admin'))
            return redirect(url_for('home'))
        else:
            flash('Senha incorreta.')
    else:
        flash('E-mail não encontrado.')

    return redirect(url_for('login'))

# -------------------------- EDIÇÃO DE DADOS --------------------------

@app.route('/editar-dados', methods=['GET', 'POST'])
def editarDados():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        novo_email = request.form['email']
        nova_senha = request.form['senha']
        nova_senha_criptografada = hashpw(nova_senha.encode('utf-8'), gensalt())
        cursor.execute("UPDATE usuario SET email = %s, senha = %s WHERE nome = %s",
                       (novo_email, nova_senha_criptografada.decode('utf-8'), session['usuario']))
        db.commit()
        flash('Dados atualizados com sucesso.')
        return redirect(url_for('home'))

    cursor.execute("SELECT email FROM usuario WHERE nome = %s", (session['usuario'],))
    usuario = cursor.fetchone()
    cursor.close()

    return render_template('editarDados.html', usuario=usuario)

# -------------------------- EXCLUIR CONTA --------------------------

@app.route('/excluir-conta', methods=['POST'])
def excluirConta():
    if 'usuario' in session:
        usuario_nome = session['usuario']
        cursor = db.cursor()
        cursor.execute("DELETE FROM usuario WHERE nome = %s", (usuario_nome,))
        db.commit()
        cursor.close()
        session.pop('usuario', None)
        flash('Sua conta foi excluída com sucesso.')
        return redirect(url_for('login'))
    return redirect(url_for('login'))

# -------------------------- ADMIN --------------------------

@app.route('/admin', methods=['GET'])
def admin():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario")
    usuarios = cursor.fetchall()
    return render_template('admin.html', usuarios=usuarios)

@app.route('/admin/excluir/<int:id>', methods=['POST'])
def excluir_usuario(id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM usuario WHERE id = %s", (id,))
    db.commit()
    flash('Usuário excluído com sucesso!')
    return redirect(url_for('admin'))

@app.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        dados = (
            request.form['nome'], request.form['sexo'], request.form['cpf'],
            request.form['data_nasc'], request.form['telefone'], request.form['pais'],
            request.form['estado'], request.form['cidade'], request.form['bairro'],
            request.form['cep'], request.form['endereco'], request.form['email']
        )
        nova_senha = request.form['senha']

        if nova_senha:
            senha_criptografada = hashpw(nova_senha.encode('utf-8'), gensalt()).decode('utf-8')
        else:
            cursor.execute("SELECT senha FROM usuario WHERE id = %s", (id,))
            senha_criptografada = cursor.fetchone()['senha']

        cursor.execute("""
            UPDATE usuario
            SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s, pais=%s,
                estado=%s, cidade=%s, bairro=%s, cep=%s, endereco=%s, email=%s, senha=%s
            WHERE id=%s
        """, (*dados, senha_criptografada, id))

        db.commit()
        flash("Dados do usuário atualizados com sucesso!")
        return redirect(url_for('admin'))

    cursor.execute("SELECT * FROM usuario WHERE id = %s", (id,))
    usuario = cursor.fetchone()
    return render_template('adminEditar.html', usuario=usuario)

# -------------------------- RECUPERAÇÃO DE SENHA --------------------------

app = Flask(__name__)

# Conexão com banco
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="sua_senha",
        database="seu_banco"
    )

@app.route("/recuperar", methods=["GET"])
def form_recuperar():
    return render_template("recuperar.html")

@app.route("/redefinir", methods=["GET"])
def form_redefinir():
    return render_template("redefinir.html")

@app.route('/recuperar-senha', methods=['POST'])
def recuperar_senha():
    data = request.get_json()
    email = data.get("email")

    reset_code = generate_reset_code(email)
    store_reset_code_in_db(email, reset_code)
    send_reset_email(email, reset_code)

    return jsonify({"message": "Código enviado para o e-mail."}), 200

@app.route('/redefinir')
def redefinir():
    return render_template("redefinir.html")

@app.route("/redefinir-senha", methods=["POST"])
def redefinir_senha():
    data = request.get_json()
    email = data.get("email")
    codigo = data.get("reset_code")
    nova_senha = data.get("nova_senha")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT reset_code FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user or user["reset_code"] != codigo:
        return jsonify({"error": "Código inválido ou e-mail não encontrado."}), 400

    senha_criptografada = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cursor.execute("UPDATE usuarios SET senha = %s, reset_code = NULL WHERE email = %s", (senha_criptografada, email))
    db.commit()
    cursor.close()
    db.close()

    return jsonify({"message": "Senha redefinida com sucesso!"})


# -------------------------- RODAR APP --------------------------

if __name__ == '__main__':
    app.run(debug=True)
