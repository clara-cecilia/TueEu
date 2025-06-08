# app/routes/admin.py
from flask import (
    Blueprint, request, session, flash,
    redirect, url_for, current_app, render_template
)
import bcrypt
from app.models import bd, registrar_log

admin = Blueprint('admin', __name__)

# =====================================================
# Painel Administrativo
# =====================================================
@admin.route('/admin')
def index():
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso restrito.", "danger")
        return redirect(url_for('auth.login'))
    return render_template('templates/admin.html')


# =====================================================
# Gerenciamento de Usuários
# =====================================================
@admin.route('/gerenciar_usuarios')
def gerenciar_usuarios():
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso negado.", "danger")
        return redirect(url_for('auth.login'))
    
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario")
    usuarios = cursor.fetchall()
    cursor.close()
    
    return render_template('gerenciarUsuarios.html', usuarios=usuarios)


@admin.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    # Verifica se o usuário logado é um administrador
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso restrito.", "danger")
        return redirect(url_for('auth.login'))
    
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE id = %s", (id,))
    usuario = cursor.fetchone()
    if not usuario:
        flash("Usuário não encontrado.", "warning")
        cursor.close()
        return redirect(url_for('admin.index'))
    
    # Processa o formulário se o método for POST
    if request.method == 'POST':
        nome = request.form['nome']
        sexo = request.form['sexo']
        cpf = request.form['cpf']
        data_nasc = request.form['data_nasc']
        telefone = request.form['telefone']
        pais = request.form['pais']
        estado = request.form['estado']
        cidade = request.form['cidade']
        cep = request.form['cep']
        email = request.form['email']
        senha = request.form.get('senha')

        if senha:
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                """
                UPDATE usuario 
                SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                    pais=%s, estado=%s, cidade=%s, cep=%s, email=%s, senha=%s
                WHERE id=%s
                """,
                (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, cep, email, senha_hash, id)
            )
        else:
            cursor.execute(
                """
                UPDATE usuario 
                SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                    pais=%s, estado=%s, cidade=%s, cep=%s, email=%s
                WHERE id=%s
                """,
                (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, cep, email, id)
            )
        bd.commit()
        cursor.close()

        registrar_log(session['usuario_id'], "usuario", id, "editado", f"Usuário {nome} atualizado.")
        flash("Usuário atualizado com sucesso.", "success")
        return redirect(url_for('admin.index'))
    
    cursor.close()
    return render_template('editarUsuario.html', usuario=usuario)


@admin.route('/excluir_usuario/<int:id>', methods=['POST'])
def excluir_usuario(id):
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso restrito.", "danger")
        return redirect(url_for('auth.login'))

    # Verifica se o usuário a ser excluído é um administrador master
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT a.is_master FROM administrador a WHERE a.usuario_id = %s", (id,))
    admin_info = cursor.fetchone()
    cursor.close()

    if admin_info and admin_info.get('is_master'):
        flash("Não é possível excluir o administrador master.", "warning")
        return redirect(url_for('admin.index'))

    cursor = bd.cursor()
    cursor.execute("DELETE FROM usuario WHERE id = %s", (id,))
    bd.commit()
    cursor.close()

    registrar_log(session['usuario_id'], "usuario", id, "excluído", "Usuário excluído pelo admin.")
    flash("Usuário excluído com sucesso!", "success")
    return redirect(url_for('admin.index'))


# =====================================================
# Gerenciamento de Administradores
# =====================================================
@admin.route('/gerenciar_adms')
def gerenciar_adms():
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso negado.", "danger")
        return redirect(url_for('auth.login'))

    cursor = bd.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.*, a.is_master 
        FROM usuario u
        INNER JOIN administrador a ON u.id = a.usuario_id
    """)
    admins = cursor.fetchall()
    cursor.close()
    
    return render_template('gerenciarAdministradores.html', admins=admins)


@admin.route('/novo_admin', methods=['POST'])
def novo_admin():
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso restrito.", "danger")
        return redirect(url_for('auth.login'))
    
    try:
        nome = request.form['nome']
        sexo = request.form['sexo']
        data_nasc = request.form['data_nasc']
        pais = request.form['pais']
        estado = request.form['estado']
        cidade = request.form['cidade']
        email = request.form['email']
        senha = request.form['senha']
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor = bd.cursor()
        sql_usuario = """
            INSERT INTO usuario (nome, sexo, data_nasc, pais, estado, cidade, email, senha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_usuario, (nome, sexo, data_nasc, pais, estado, cidade, email, senha_hash))
        bd.commit()
        novo_usuario_id = cursor.lastrowid

        sql_admin = "INSERT INTO administrador (usuario_id, is_master) VALUES (%s, %s)"
        cursor.execute(sql_admin, (novo_usuario_id, 0))
        bd.commit()
        cursor.close()

        registrar_log(session['usuario_id'], "administrador", novo_usuario_id, "criado", f"Administrador {nome} cadastrado.")
        flash("Administrador cadastrado com sucesso!", "success")
    except Exception as erro:
        flash("Erro ao cadastrar administrador: " + str(erro), "danger")
    
    return redirect(url_for('admin.gerenciar_adms'))
