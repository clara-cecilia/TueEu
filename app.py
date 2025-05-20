from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import bcrypt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import smtplib
from email.mime.text import MIMEText
import random
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.secret_key = 'chave_secreta'

# ============================================
# CONEXÃO COM O BANCO DE DADOS
# ============================================
def conectar_bd():
    try:
        banco = mysql.connector.connect(
            host="localhost",
            user="root",
            password="280697",
            port='3306',
            database="cadastro_TueEu"
        )
        print("Conexão realizada com sucesso!")
        return banco
    except mysql.connector.Error as err:
        print(f"Erro na conexão: {err}")
        return None

bd = conectar_bd()

# ============================================
# FUNÇÕES AUXILIARES - RESET DE SENHA
# ============================================
def gerar_codigo_reset():
    return str(random.randint(100000, 999999))

def armazenar_codigo_reset_no_bd(email, codigo):
    # Busca o ID do usuário com base no email
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT id FROM usuario WHERE email = %s", (email,))
    usuario = cursor.fetchone()
    if not usuario:
        cursor.close()
        return False  # Usuário não encontrado
    usuario_id = usuario['id']
    cursor.close()
    
    # Exclui resets anteriores e insere o novo registro usando o usuario_id
    cursor = bd.cursor()
    cursor.execute("DELETE FROM reset_senhas WHERE usuario_id = %s", (usuario_id,))
    expiracao = datetime.now() + timedelta(minutes=10)
    cursor.execute(
        "INSERT INTO reset_senhas (usuario_id, codigo, expiracao) VALUES (%s, %s, %s)",
        (usuario_id, codigo, expiracao)
    )
    bd.commit()
    cursor.close()
    return True

def enviar_email_reset(email, codigo):
    remetente = "6tueeu6@gmail.com"
    senha_remetente = "izctformdfbzieot"
    mensagem = MIMEText(f"Seu código de recuperação é: {codigo}", "plain")
    mensagem["Subject"] = "Recuperação de senha"
    mensagem["From"] = remetente
    mensagem["To"] = email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(remetente, senha_remetente)
            servidor.send_message(mensagem)
        print(f"E-mail de recuperação enviado para {email} com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail de recuperação: {e}")

def verificar_codigo_reset(email, codigo):
    # Obtém o ID do usuário com base no email
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT id FROM usuario WHERE email = %s", (email,))
    usuario = cursor.fetchone()
    if not usuario:
        cursor.close()
        return False
    usuario_id = usuario['id']
    cursor.close()
    
    # Verifica se há um reset válido para o usuário
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reset_senhas WHERE usuario_id = %s AND codigo = %s", (usuario_id, codigo))
    resultado = cursor.fetchone()
    cursor.close()
    if resultado and resultado["expiracao"] > datetime.now():
        return True
    return False

def redefinir_senha(email, nova_senha):
    nova_senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor = bd.cursor()
    cursor.execute("UPDATE usuario SET senha = %s WHERE email = %s", (nova_senha_hash, email))
    bd.commit()
    # Opcional: Exclui registros antigos de reset para esse usuário
    cursor.execute("DELETE FROM reset_senhas WHERE usuario_id = (SELECT id FROM usuario WHERE email = %s)", (email,))
    bd.commit()
    cursor.close()

# ============================================
# FUNÇÕES AUXILIARES - CONFIRMAÇÃO DE E-MAIL (DOUBLE OPT-IN)
# ============================================
def gerar_token_confirmacao(email):
    serializer = URLSafeTimedSerializer(app.secret_key)
    return serializer.dumps(email, salt='email-confirm-salt')

def enviar_email_confirmacao(email):
    token = gerar_token_confirmacao(email)
    url_confirmacao = url_for('confirm_email', token=token, _external=True)
    html = f"""
    <html>
      <body>
        <p>Para confirmar seu cadastro, clique no link abaixo:</p>
        <p><a href="{url_confirmacao}">Confirmar E-mail</a></p>
      </body>
    </html>
    """
    remetente = "6tueeu6@gmail.com"
    senha_remetente = "izctformdfbzieot"
    mensagem = MIMEText(html, 'html')
    mensagem["Subject"] = "Confirmação de Cadastro"
    mensagem["From"] = remetente
    mensagem["To"] = email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=60) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.ehlo()
            servidor.login(remetente, senha_remetente)
            servidor.send_message(mensagem)
        print(f"E-mail de confirmação enviado para {email} com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail de confirmação: {e}")

@app.route('/confirm/<token>')
def confirm_email(token):
    serializer = URLSafeTimedSerializer(app.secret_key)
    try:
        email = serializer.loads(token, salt='email-confirm-salt', max_age=3600)
    except SignatureExpired:
        flash('O link de confirmação expirou. Cadastre-se novamente.')
        return redirect(url_for('cadastro'))
    except BadSignature:
        flash('Link inválido.')
        return redirect(url_for('index'))
    cursor = bd.cursor()
    cursor.execute("UPDATE usuario SET email_verificado = 1 WHERE email = %s", (email,))
    bd.commit()
    cursor.close()
    flash('E-mail confirmado com sucesso! Agora você pode fazer login.')
    return redirect(url_for('login'))

# ============================================
# ROTAS PÚBLICAS (Páginas)
# ============================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

@app.route('/login')
def login():
    return render_template('login.html')

# Rota para a página de "Esqueceu sua senha?" – usando o mesmo nome do arquivo "esqueceuSenha.html"
@app.route('/esqueceu-senha')
def esqueceuSenha():
    return render_template('esqueceuSenha.html')

# Rota para a página de recuperação (formulário para inserir e-mail) – "recuperar.html"
@app.route('/recuperar')
def recuperar():
    return render_template('recuperar.html')

# Rota para a página de redefinição (formulário para inserir reset code e nova senha) – "redefinir.html"
@app.route('/redefinir')
def redefinir():
    return render_template('redefinir.html')

@app.route('/home')
def home():
    if 'usuario' in session:
        return render_template('home.html', usuario=session['usuario'])
    return redirect(url_for('index'))

# Rota para o próprio usuário editar seus dados – usando "editarDados.html"
@app.route('/editarDados', methods=['GET', 'POST'])
def editarDados():
    if 'user_id' not in session:
        flash("Você precisa estar logado para editar seus dados.")
        return redirect(url_for('login'))
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE id = %s", (session['user_id'],))
    usuario = cursor.fetchone()
    cursor.close()
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
        senha = request.form.get('senha')
        cursor = bd.cursor()
        if senha:
            cursor.execute("""
                UPDATE usuario SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                pais=%s, estado=%s, cidade=%s, bairro=%s, cep=%s, endereco=%s, email=%s, senha=SHA2(%s, 256)
                WHERE id=%s
            """, (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, bairro, cep, endereco, email, senha, session['user_id']))
        else:
            cursor.execute("""
                UPDATE usuario SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                pais=%s, estado=%s, cidade=%s, bairro=%s, cep=%s, endereco=%s, email=%s
                WHERE id=%s
            """, (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, bairro, cep, endereco, email, session['user_id']))
        bd.commit()
        cursor.close()
        flash("Dados atualizados com sucesso.")
        return redirect(url_for('home'))
    return render_template('editarDados.html', usuario=usuario)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('user_id', None)
    flash('Você saiu do sistema.')
    return redirect(url_for('login'))

# ============================================
# ROTAS DE AUTENTICAÇÃO (Cadastro e Login)
# ============================================
@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    email = request.form.get('email')
    nome = request.form.get('nome')
    if not email:
        flash("Erro: E-mail não informado no formulário.")
        return redirect(url_for("cadastro"))
    
    # Verifica se o e-mail já existe
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT id FROM usuario WHERE email = %s", (email,))
    if cursor.fetchone():
        flash("Este e-mail já está cadastrado. Faça login ou use outro e-mail.")
        cursor.close()
        return redirect(url_for("cadastro"))
    cursor.close()

    cursor = bd.cursor()
    senha_criptografada = bcrypt.hashpw(request.form['senha'].encode('utf-8'), bcrypt.gensalt())
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
        email,
        senha_criptografada
    )
    sql = """
    INSERT INTO usuario (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, bairro, cep, endereco, email, senha)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, dados)
    bd.commit()
    cursor.close()

    enviar_email_confirmacao(email)
    flash('Cadastro efetuado! Verifique seu e-mail para confirmar o cadastro.')
    return redirect(url_for('index'))

@app.route('/logar', methods=['POST'])
def logar():
    email = request.form['email']
    senha = request.form['senha']
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE email = %s", (email,))
    usuario = cursor.fetchone()
    cursor.close()
    if usuario:
        if usuario.get('email_verificado', 0) != 1:
            flash('Por favor, confirme seu e-mail antes de fazer login.')
            return redirect(url_for('login'))
        senha_armazenada = usuario['senha']
        if bcrypt.checkpw(senha.encode('utf-8'), senha_armazenada.encode('utf-8')):
            session['usuario'] = usuario['nome']
            session['user_id'] = usuario['id']
            session['is_admin'] = usuario.get('is_admin', 0)
            flash('Login realizado com sucesso!')
            if usuario.get('is_admin', 0) == 1:
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('home'))
        flash('Senha incorreta.')
    else:
        flash('E-mail não encontrado.')
    return redirect(url_for('login'))

# ============================================
# ROTAS DE RECUPERAÇÃO DE SENHA
# ============================================
@app.route('/recuperar-senha', methods=['POST'])
def recuperar_senha():
    dados = request.get_json()
    email = dados.get("email")
    codigo_reset = gerar_codigo_reset()
    if not armazenar_codigo_reset_no_bd(email, codigo_reset):
        return jsonify({"error": "Usuário não encontrado."}), 400
    enviar_email_reset(email, codigo_reset)
    return jsonify({"message": "Código enviado para o e-mail."}), 200

@app.route("/redefinir-senha", methods=["POST"])
def redefinir_senha():
    dados = request.get_json()
    email = dados.get("email")
    codigo = dados.get("reset_code")
    nova_senha = dados.get("nova_senha")
    if verificar_codigo_reset(email, codigo):
        redefinir_senha(email, nova_senha)
        return jsonify({"message": "Senha redefinida com sucesso!"})
    return jsonify({"error": "Código inválido ou e-mail não encontrado."}), 400

# ============================================
# ROTAS ADMINISTRATIVAS
# ============================================
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
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE is_admin = 0")
    usuarios = cursor.fetchall()
    cursor.close()
    return render_template('gerenciarUsuarios.html', usuarios=usuarios)

@app.route('/gerenciarAdms')
def gerenciarAdms():
    if not session.get('is_admin'):
        flash("Acesso negado.")
        return redirect(url_for('login'))
    cursor = bd.cursor(dictionary=True)
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
        cursor = bd.cursor()
        cursor.execute("""
            INSERT INTO usuario 
            (nome, sexo, data_nasc, pais, estado, cidade, bairro, email, senha, is_admin, is_master_admin) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 0)
        """, (nome, sexo, data_nasc, pais, estado, cidade, bairro, email, senha_hash))
        bd.commit()
        cursor.close()
        flash("Administrador cadastrado com sucesso!", "sucesso")
    except Exception as e:
        flash("Erro ao cadastrar administrador: " + str(e), "erro")
    return redirect(url_for('gerenciarAdms'))

@app.route('/editarUsuario/<int:id>', methods=['GET', 'POST'])
def editarUsuario(id):
    if 'usuario' not in session or not session.get('is_admin'):
        flash("Acesso restrito.")
        return redirect(url_for('login'))
    cursor = bd.cursor(dictionary=True)
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
        bd.commit()
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
    cursor = bd.cursor()
    # Prevenir exclusão do administrador master (por exemplo: id=1)
    if id == 1:
        flash("Não é possível excluir o administrador master.")
        return redirect(url_for('admin'))
    cursor.execute("DELETE FROM usuario WHERE id = %s", (id,))
    bd.commit()
    cursor.close()
    flash("Usuário excluído com sucesso.")
    return redirect(url_for('admin'))

# ============================================
# EXECUÇÃO DA APLICAÇÃO
# ============================================
if __name__ == '__main__':
    app.run(debug=True)
