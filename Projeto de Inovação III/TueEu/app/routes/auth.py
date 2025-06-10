# app/routes/auth.py
from flask import (
    Blueprint, request, session, flash, redirect,
    url_for, current_app, render_template
)
import bcrypt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.models import bd, registrar_log
from app.utils import enviar_email_confirmacao, enviar_email_reset
from flask import jsonify
from app.utils import enviar_email, enviar_email_reativacao


auth = Blueprint('auth', __name__)

# ============================================================
# Cadastro e Confirmação de E-mail
# ============================================================
@auth.route('/cadastro', methods=['GET'])
def cadastro():
    return render_template('auth/cadastro.html')

@auth.route('/cadastrar', methods=['POST'])
def cadastrar():
    email = request.form.get('email')
    nome = request.form.get('nome')

    if not email:
        flash("Erro: E-mail não informado no formulário.", "danger")
        return redirect(url_for("auth.cadastro"))

    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT id FROM usuario WHERE email = %s", (email,))
    if cursor.fetchone():
        flash("Este e-mail já está cadastrado. Faça login ou use outro e-mail.", "warning")
        cursor.close()
        return redirect(url_for("auth.cadastro"))
    cursor.close()

    cursor = bd.cursor()
    senha_criptografada = bcrypt.hashpw(
        request.form['senha'].encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    dados = (
        request.form['nome'],
        request.form['sexo'],
        request.form['cpf'],
        request.form['data_nasc'],
        request.form['telefone'],
        request.form['pais'],
        request.form['estado'],
        request.form['cidade'],
        request.form['cep'],
        email,
        senha_criptografada
    )

    sql = """
    INSERT INTO usuario (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, cep, email, senha)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, dados)
    bd.commit()
    usuario_id = cursor.lastrowid
    cursor.close()

    enviar_email_confirmacao(email)
    registrar_log(usuario_id, "usuario", usuario_id, "criado", f"Usuário {nome} cadastrado.")
    flash('Cadastro efetuado! Verifique seu e-mail para confirmar o cadastro.', "success")
    return redirect(url_for('auth.login'))

@auth.route('/confirmar_email/<token>')
def confirmar_email(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='confirmacao-email-salt', max_age=3600)
    except SignatureExpired:
        flash('O link de confirmação expirou. Cadastre-se novamente.', 'danger')
        return redirect(url_for('auth.cadastro'))
    except BadSignature:
        flash('Link inválido.', 'danger')
        return redirect(url_for('auth.login'))

    cursor = bd.cursor()
    cursor.execute("UPDATE usuario SET email_verificado = 1 WHERE email = %s", (email,))
    bd.commit()
    cursor.close()
    
    flash('E-mail confirmado com sucesso! Agora você pode fazer login.', 'success')
    registrar_log(None, "usuario", None, "email confirmado", f"E-mail: {email}")
    return redirect(url_for('auth.login'))

# ============================================================
# Login
# ============================================================
@auth.route('/login', methods=['GET'])
def login():
    return render_template('auth/login.html')

@auth.route('/logar', methods=['POST'])
def logar():
    email = request.form['email']
    senha = request.form['senha']

    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE email = %s", (email,))
    usuario = cursor.fetchone()
    cursor.close()

    if not usuario:
        flash('E-mail ou senha inválidos', 'danger')
        return redirect(url_for('auth.login'))

    if not usuario.get('email_verificado'):
        flash('Por favor, confirme seu e-mail antes de fazer login.', 'warning')
        return redirect(url_for('auth.login'))
    # Verifica se a conta está inativa
    if usuario.get('status') != 'ativo':
        flash('Sua conta está inativa. Por favor, confirme a reativação no aviso abaixo.', 'warning')
        # Em vez de redirecionar, renderiza a tela de login com uma variável extra
        return render_template('auth/login.html', inativo=True, email=email)


    if not bcrypt.checkpw(senha.encode('utf-8'), usuario['senha'].encode('utf-8')):
        flash('E-mail ou senha inválidos', 'danger')
        return redirect(url_for('auth.login'))

    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT is_master FROM administrador WHERE usuario_id = %s", (usuario['id'],))
    admin = cursor.fetchone()
    cursor.close()

    session['usuario_id']    = usuario['id']
    session['usuario_email'] = usuario['email']
    session['usuario_nome'] = usuario['nome']  # <-- Adicionado para armazenar o nome do usuário na sessão
    session['is_admin']      = bool(admin)
    session['is_master']     = admin['is_master'] if admin else 0

    registrar_log(usuario['id'], "usuario", usuario['id'], "login", f"Usuário {usuario['nome']} efetuou login.")
    flash('Login realizado com sucesso!', 'success')

    # Redireciona para o painel administrativo se for admin
    if admin:
        return redirect(url_for('admin.home'))
    return redirect(url_for('auth.home'))

@auth.route('/logout')
def logout():
    session.clear()
    flash('Você saiu com sucesso.', 'info')
    return redirect(url_for('auth.login'))
@auth.route('/solicitar_reativacao_ajax', methods=['POST'])
def solicitar_reativacao_ajax():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"message": "E-mail não informado."}), 400

    # Procura por um usuário inativo com esse e‑mail
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE email = %s AND status != 'ativo'", (email,))
    usuario = cursor.fetchone()
    cursor.close()

    if not usuario:
        return jsonify({"message": "Nenhuma conta inativa encontrada com esse e-mail."}), 400

    # Gerar token usando um salt exclusivo para reativação
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps(email, salt='reativar-conta-salt')
    # Função para enviar e-mail de reativação (reutilize sua função já existente ou similar)
    enviar_email_reativacao(email, token)
    return jsonify({"message": "Um e-mail com as instruções para reativação foi enviado."})
@auth.route('/reativar_conta/<token>')
def reativar_conta(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        # Utilize o mesmo salt que usamos para gerar o token
        email = serializer.loads(token, salt='reativar-conta-salt', max_age=3600)
    except SignatureExpired:
        flash('O link de reativação expirou. Solicite novamente.', 'danger')
        return redirect(url_for('auth.solicitar_reativacao'))
    except BadSignature:
        flash('Link de reativação inválido.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Atualizar o status para 'ativo'
    cursor = bd.cursor()
    cursor.execute("UPDATE usuario SET status = 'ativo' WHERE email = %s", (email,))
    bd.commit()
    cursor.close()
    
    flash('Sua conta foi reativada com sucesso! Faça login para continuar.', 'success')
    registrar_log(None, "usuario", None, "reativado", f"E-mail reativado: {email}")
    return redirect(url_for('auth.login'))

@auth.route('/solicitar_reativacao', methods=['GET', 'POST'])
def solicitar_reativacao():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Busca o usuário que esteja inativo, somente se realmente existir
        cursor = bd.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuario WHERE email = %s AND status != 'ativo'", (email,))
        usuario = cursor.fetchone()
        cursor.close()
        
        if not usuario:
            flash('Nenhuma conta inativa encontrada com esse e-mail.', 'danger')
            return redirect(url_for('auth.solicitar_reativacao'))
        
        # Gerar token usando um salt exclusivo para reativação
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps(email, salt='reativar-conta-salt')
        # Função para enviar o e-mail de reativação (você pode reusar a lógica do enviar_email_confirmacao)
        enviar_email_reativacao(email, token)
        
        flash('Um e-mail com as instruções para reativação foi enviado.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/solicitar_reativacao.html')
# ============================================================
# Recuperação e Redefinição de Senha
# ============================================================
@auth.route('/recuperar_senha', methods=['GET', 'POST'])
def recuperar_senha():
    if request.method == 'POST':
        email = request.form.get("email")
        cursor = bd.cursor(dictionary=True)
        cursor.execute("SELECT id FROM usuario WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        cursor.close()

        if not usuario:
            flash("Usuário não encontrado.", "warning")
            return redirect(url_for('auth.recuperar_senha'))

        enviar_email_reset(email)
        flash("Link de redefinição enviado! Confira seu e‑mail.", "info")
        return redirect(url_for('auth.login'))

    return render_template('auth/recuperarSenha.html')

@auth.route('/confirmar_reset/<token>')
def confirmar_reset(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        serializer.loads(token, salt='reset-password-salt', max_age=3600)
    except SignatureExpired:
        flash("Link expirado. Solicite uma nova redefinição de senha.", "danger")
        return redirect(url_for('auth.recuperar_senha'))
    except BadSignature:
        flash("Link inválido. Solicite uma nova redefinição de senha.", "danger")
        return redirect(url_for('auth.recuperar_senha'))

    return render_template('auth/redefinirSenha.html', token=token)

@auth.route('/definir_senha', methods=['POST'])
def definir_senha():
    token = request.form.get("token")
    nova_senha = request.form.get("nova_senha")
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    try:
        email = serializer.loads(token, salt='reset-password-salt', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash("Link inválido ou expirado. Solicite redefinição novamente.", "danger")
        return redirect(url_for('auth.recuperar_senha'))

    senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cursor = bd.cursor()
    cursor.execute("UPDATE usuario SET senha = %s WHERE email = %s", (senha_hash, email))
    bd.commit()
    cursor.close()

    flash("Senha redefinida com sucesso. Faça login.", "success")
    return redirect(url_for('auth.login'))

# ============================================================
# Rotas Extras: Home e Edição de Dados
# ============================================================
@auth.route('/home')
def home():
    if 'usuario_nome' in session:
        return render_template('user/home.html', usuario=session['usuario_nome'])
    return redirect(url_for('auth.login'))

@auth.route('/editar_dados', methods=['GET', 'POST'])
def editar_dados():
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para editar seus dados.", "warning")
        return redirect(url_for('auth.login'))

    user_id = session['usuario_id']
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE id = %s", (user_id,))
    usuario = cursor.fetchone()
    cursor.close()

    if request.method == 'POST':
        novo_nome       = request.form.get('nome')
        nova_data_nasc  = request.form.get('data_nasc')
        novo_telefone   = request.form.get('telefone')
        novo_sexo       = request.form.get('sexo')
        novo_pais       = request.form.get('pais')
        novo_estado     = request.form.get('estado')
        nova_cidade     = request.form.get('cidade')
        novo_cep        = request.form.get('cep')
        novo_email      = request.form.get('email')
        senha_fornecida = request.form.get('senha')

        if not senha_fornecida:
            flash("Você precisa informar sua senha para confirmar as alterações.", "danger")
            return redirect(url_for('auth.editar_dados'))

        if not bcrypt.checkpw(senha_fornecida.encode('utf-8'), usuario['senha'].encode('utf-8')):
            flash("Senha incorreta. Por favor, tente novamente.", "danger")
            return redirect(url_for('auth.editar_dados'))

        email_verificado = usuario['email_verificado']
        if novo_email != usuario['email']:
            email_verificado = 0
            session['usuario_email'] = novo_email
            enviar_email_confirmacao(novo_email)

        cursor = bd.cursor()
        sql = """
            UPDATE usuario
            SET nome = %s, data_nasc = %s, telefone = %s, sexo = %s, pais = %s,
                estado = %s, cidade = %s, cep = %s, email = %s, email_verificado = %s
            WHERE id = %s
        """
        valores = (
            novo_nome, nova_data_nasc, novo_telefone, novo_sexo, novo_pais,
            novo_estado, nova_cidade, novo_cep, novo_email, email_verificado, user_id
        )
        cursor.execute(sql, valores)
        bd.commit()
        cursor.close()

        registrar_log(user_id, "usuario", user_id, "editado", f"Usuário {novo_nome} editou seus dados.")
        flash("Dados atualizados com sucesso!", "success")
        if novo_email != usuario['email']:
            flash("Um e-mail de validação foi enviado para o seu novo endereço. Por favor, confirme seu e-mail.", "warning")
        return redirect(url_for('auth.home'))

    return render_template('user/editarDados.html', usuario=usuario)
@auth.route('/desativar_conta', methods=['POST'])
def desativar_conta():
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para realizar essa ação.", "warning")
        return redirect(url_for('auth.login'))
    
    user_id = session['usuario_id']
    cursor = bd.cursor()
    cursor.execute("UPDATE usuario SET status = 'inativo' WHERE id = %s", (user_id,))
    bd.commit()
    cursor.close()

    registrar_log(user_id, "usuario", user_id, "desativado", "Conta desativada pelo usuário.")

    # Limpa a sessão (logout)
    session.clear()
    flash("Sua conta foi desativada e você foi deslogado.", "success")
    return redirect(url_for('auth.login'))