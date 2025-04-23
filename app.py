from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from bcrypt import hashpw, gensalt , checkpw
import hashlib
# from reset_utils import generate_reset_code, store_reset_code_in_db, send_reset_email, verify_reset_code, reset_password

app = Flask(__name__)
app.secret_key = 'chave_secreta' # Necessária para usar sessões
#
#conexão com banco de dados 
#
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
#
#criação de rotas das paginas 
#
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
#
#cadastrar usuario no banco de dados 
#
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

        # Criptografa a senha antes de salvar
    senha_criptografada = hashpw(dados[-1].encode('utf-8'), gensalt())
    
    # Substitui a senha original pela senha criptografada
    dados = (*dados[:-1], senha_criptografada)

    sql = '''
    INSERT INTO usuario (
        nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade,
        bairro, cep, endereco, email, senha
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    print("Requisição recebida!")
    cursor.execute(sql, dados)
    db.commit()
    cursor.close()
    return redirect('/')
#
# pagina de login, validação do e-mail e senha.
#
@app.route('/logar', methods=['POST'])
def logar():
    email = request.form['email']
    senha = request.form['senha']

    cursor = db.cursor(dictionary=True)    
    cursor.execute("SELECT * FROM usuario WHERE email = %s", (email,))
    usuario = cursor.fetchone()

    if usuario:
        # Recupera o hash da senha armazenado no banco
        senha_armazenada = usuario['senha']
        
        # Verifica se a senha fornecida corresponde ao hash
        if checkpw(senha.encode('utf-8'), senha_armazenada.encode('utf-8')):
            session['usuario'] = usuario['nome']  # Salva o nome do usuário na sessão
            session['is_admin'] = usuario['is_admin']

            if usuario['is_admin'] ==1:
                flash('Login realizado como administrator!')
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Senha incorreta.')  # Senha inválida
    else:
        flash('E-mail não encontrado.')  # Email não existe no banco

    return redirect(url_for('login'))  # Redireciona para a página de login em caso de falha
    
@app.route('/home')
def home():
    if 'usuario' in session:
        return render_template('home.html', usuario=session['usuario'])
    else:
        return redirect(url_for('login'))


@app.route('/editar-dados', methods=['GET', 'POST'])
def editarDados():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        novo_email = request.form['email']
        nova_senha = request.form['senha']

        # Criptografa a nova senha antes de atualizar no banco
        nova_senha_criptografada = hashpw(nova_senha.encode('utf-8'), gensalt())

        # Atualiza o email e a senha no banco de dados
        cursor.execute("UPDATE usuario SET email = %s, senha = %s WHERE nome = %s", 
                       (novo_email, nova_senha_criptografada.decode('utf-8'), session['usuario']))
        db.commit()
        flash('Dados atualizados com sucesso.')
        return redirect(url_for('home'))

    # Se GET, mostrar os dados atuais
    cursor.execute("SELECT email, senha FROM usuario WHERE nome = %s", (session['usuario'],))
    usuario = cursor.fetchone()
    cursor.close()

    return render_template('editarDados.html', usuario=usuario)
#
# usuario excluir a conta
#
@app.route('/excluir-conta', methods=['POST'])
def excluirConta():
    if 'usuario' in session:
        usuario_nome = session['usuario']

        cursor = db.cursor()

        # Busca o e-mail com base no nome da sessão
        cursor.execute("SELECT email FROM usuario WHERE nome = %s", (usuario_nome,))
        resultado = cursor.fetchone()

        if resultado:
            email = resultado[0]
            # Exclui o usuário
            cursor.execute("DELETE FROM usuario WHERE email = %s", (email,))
            db.commit()
            cursor.close()

            session.pop('usuario', None)
            flash('Sua conta foi excluída com sucesso.')
            return redirect(url_for('login'))
        else:
            flash('Erro ao localizar usuário.')
            return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))
    
# Pagina do administrador 

# Ver usuarios
@app.route('/admin', methods=['GET'])
def admin():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario")
    usuarios = cursor.fetchall()

    return render_template('admin.html', usuarios=usuarios)

#adm excluir usuarios
@app.route('/admin/excluir/<int:id>', methods=['POST'])
def excluir_usuario(id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM usuario WHERE id = %s",(id,))
    db.commit()

    flash('Usuário excluído com sucesso!')
    return redirect(url_for('admin'))

#adm editar usuarios
@app.route('/admin/editar/<int:id>', methods=['GET','POST'])
def editar_usuario(id):
    cursor = db.cursor(dictionary=True)

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
            nova_senha = request.form['senha']
        
            if nova_senha:
                senha_criptografada = hashpw(nova_senha.encode('utf-8'), gensalt()).decode('utf-8')
            else:
                cursor.execute("SELECT senha FROM usuario WHERE id = %s",(id))
                senha_criptografada = cursor.fetchone()['senha']

        
            cursor.execute("""
                 UPDATE usuario
                 SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s, pais=%s, estado=%s, cidade=%s, bairro=%s, cep=%s, endereco=%s, email=%s, senha=%s 
                WHERE id=%s
                """,(nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, bairro, cep, endereco, email, senha_criptografada, id))
        

            db.commit()
            flash("Dados do usuario atualizado com sucesso!")
            return redirect(url_for('admin'))
    
    cursor.execute("SELECT * FROM usuario WHERE id = %s",(id,))
    usuario = cursor.fetchone()

    return render_template('adminEditar.html', usuario=usuario)


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Você saiu do sistema.')
    return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(debug=True)


app = Flask(__name__)

@app.route('/')
def home():
    return render_template("recuperar.html")

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

@app.route('/redefinir-senha', methods=['POST'])
def redefinir_senha():
    data = request.get_json()
    email = data.get("email")
    reset_code = data.get("reset_code")
    nova_senha = data.get("nova_senha")

    if not verify_reset_code(email, reset_code):
        return jsonify({"error": "Código inválido ou expirado"}), 400

    reset_password(email, nova_senha)
    return jsonify({"message": "Senha redefinida com sucesso!"}), 200

if __name__ == "__main__":
    app.run(debug=True)
