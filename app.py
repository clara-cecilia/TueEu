from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import bcrypt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'chave_secreta'  # Idealmente, use uma variável de ambiente para essa chave

# ============================================
# CONEXÃO COM O BANCO DE DADOS
# ============================================
def conectar_bd():
    try:
        banco = mysql.connector.connect(
            host="localhost",
            user="root",
            password="2904",
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
# NOVAS FUNÇÕES AUXILIARES - RECUPERAÇÃO DE SENHA (DOUBLE OPT-IN)
# ============================================
def gerar_token_reset(email):
    serializer = URLSafeTimedSerializer(app.secret_key)
    return serializer.dumps(email, salt='reset-password-salt')

def enviar_email_reset(email, reset_link):
    html = f"""
    <html>
      <body>
        <p>Para redefinir sua senha, clique no link abaixo:</p>
        <p><a href="{reset_link}">Redefinir Senha</a></p>
        <p>Este link expira em 1 hora.</p>
      </body>
    </html>
    """
    remetente = "6tueeu6@gmail.com"
    senha_remetente = "izctformdfbzieot"
    mensagem = MIMEText(html, 'html')
    mensagem["Subject"] = "Redefinição de Senha"
    mensagem["From"] = remetente
    mensagem["To"] = email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=60) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.ehlo()
            servidor.login(remetente, senha_remetente)
            servidor.send_message(mensagem)
        print(f"E-mail de redefinição enviado para {email} com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail de redefinição: {e}")

# ============================================
# ROTAS PÚBLICAS (Páginas)
# ============================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    email = request.form.get('email')
    nome = request.form.get('nome')
    if not email:
        flash("Erro: E-mail não informado no formulário.")
        return redirect(url_for("cadastro"))
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

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

# Rota para processar o login (POST)
@app.route('/logar', methods=['GET', 'POST'])
def logar():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conexao = conectar_bd()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("SELECT * FROM usuario WHERE email = %s", (email,))
        usuario = cursor.fetchone()

        if usuario and bcrypt.checkpw(senha.encode('utf-8'), usuario['senha'].encode('utf-8')):
            cursor.execute("SELECT is_master FROM administrador WHERE usuario_id = %s", (usuario['id'],))
            admin = cursor.fetchone()

            session['usuario_id'] = usuario['id']
            session['usuario_email'] = usuario['email']
            session['is_admin'] = bool(admin)
            session['is_master'] = admin['is_master'] if admin else 0

            flash('Login realizado com sucesso!', 'success')

            if admin:
                # Se for administrador
                return redirect(url_for('admin'))
            else:
                # Se for usuário comum
                return redirect(url_for('home'))
        else:
            flash('E-mail ou senha inválidos', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

# Novo fluxo para recuperação de senha com double opt‑in:
@app.route('/recuperar-senha', methods=['GET', 'POST'])
def recuperar_senha():
    if request.method == 'POST':
        email = request.form.get("email")
        cursor = bd.cursor(dictionary=True)
        cursor.execute("SELECT id FROM usuario WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        cursor.close()
        if usuario is None:
            flash("Usuário não encontrado.")
            return redirect(url_for('recuperar_senha'))
        token = gerar_token_reset(email)
        reset_link = url_for('confirm_reset', token=token, _external=True)
        enviar_email_reset(email, reset_link)
        flash("Link de redefinição enviado! Confira seu e‑mail.")
        # Após enviar o link, redireciona para a página de login
        return redirect(url_for('login'))
    return render_template('recuperarSenha.html')


# Rota que valida o token e exibe o formulário para definir a nova senha
@app.route('/confirm-reset/<token>', methods=['GET'])
def confirm_reset(token):
    serializer = URLSafeTimedSerializer(app.secret_key)
    try:
        serializer.loads(token, salt='reset-password-salt', max_age=3600)
    except SignatureExpired:
        flash("Link expirado. Solicite uma nova redefinição de senha.")
        return redirect(url_for('recuperar_senha'))
    except BadSignature:
        flash("Link inválido. Solicite uma nova redefinição de senha.")
        return redirect(url_for('recuperar_senha'))
    return render_template('redefinirSenha.html', token=token)

# Rota que recebe a nova senha e atualiza no banco de dados
@app.route('/definir-senha', methods=['POST'])
def definir_senha():
    token = request.form.get("token")
    nova_senha = request.form.get("nova_senha")
    serializer = URLSafeTimedSerializer(app.secret_key)
    try:
        email = serializer.loads(token, salt='reset-password-salt', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash("Link inválido ou expirado. Solicite redefinição novamente.")
        return redirect(url_for('recuperar_senha'))
    senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor = bd.cursor()
    cursor.execute("UPDATE usuario SET senha = %s WHERE email = %s", (senha_hash, email))
    bd.commit()
    cursor.close()
    flash("Senha redefinida com sucesso. Faça login.")
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'usuario_email' in session:
        return render_template('home.html', usuario=session['usuario_email'])

    return redirect(url_for('index'))

# Rota para o próprio usuário editar seus dados – usando "editarDados.html"
@app.route('/editarDados', methods=['GET', 'POST'])
def editarDados():
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para editar seus dados.")
        return redirect(url_for('login'))
    
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE id = %s", (session['usuario_id'],))
    usuario = cursor.fetchone()
    cursor.close()
    
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        cursor = bd.cursor()
        if senha:
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("UPDATE usuario SET email = %s, senha = %s WHERE id = %s", 
                           (email, senha_hash, session['usuario_id']))
        else:
            cursor.execute("UPDATE usuario SET email = %s WHERE id = %s", 
                           (email, session['usuario_id']))
        bd.commit()
        cursor.close()
        flash("Dados atualizados com sucesso.")
        return redirect(url_for('home'))
    
    return render_template('editarDados.html', usuario=usuario)

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu com sucesso.', 'info')
    return redirect(url_for('login'))

# ============================================
# ROTAS ADMINISTRATIVAS
# ============================================
@app.route('/admin')
def admin():
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso restrito.")
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/gerenciarUsuarios')
def gerenciarUsuarios():
    if not session.get('is_admin'):
        flash("Acesso negado.")
        return redirect(url_for('login'))
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario")
    usuarios = cursor.fetchall()
    cursor.close()
    return render_template('gerenciarUsuarios.html', usuarios=usuarios)

@app.route('/gerenciarAdms')
def gerenciarAdms():
    if not session.get('is_admin'):
        flash("Acesso negado.")
        return redirect(url_for('login'))

    cursor = bd.cursor(dictionary=True)

    # Buscar usuários que são administradores, juntando as tabelas
    cursor.execute("""
        SELECT u.*, a.is_master
        FROM usuario u
        INNER JOIN administrador a ON u.id = a.usuario_id
    """)
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
        senha = request.form.get('senha')
        if senha:
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("""
                UPDATE usuario 
                SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                    pais=%s, estado=%s, cidade=%s, bairro=%s, cep=%s, endereco=%s, email=%s, senha=%s
                WHERE id=%s
            """, (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, bairro, cep, endereco, email, senha_hash, id))
        else:
            cursor.execute("""
                UPDATE usuario 
                SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
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
