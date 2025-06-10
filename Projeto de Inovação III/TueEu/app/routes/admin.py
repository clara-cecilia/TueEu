# app/routes/admin.py
from flask import (
    Blueprint, request, session, flash,
    redirect, url_for, current_app, render_template
)
import bcrypt
from app.models import bd, registrar_log
from app.utils import requer_master  # decorador definido em utils.py

admin = Blueprint('admin', __name__)

# =====================================================
# Painel Administrativo
# =====================================================
@admin.route('/admin')
def home():
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso restrito.", "danger")
        return redirect(url_for('auth.login'))
    return render_template('admin/homeAdm.html')


# =====================================================
# Gerenciamento de Usuários
# (Admin Master e Normal: ver, editar e excluir)
# =====================================================
@admin.route('/gerenciar_usuarios')
def gerenciar_usuarios():
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso negado.", "danger")
        return redirect(url_for('auth.login'))
    
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE id NOT IN (SELECT usuario_id FROM administrador)")    
    usuarios = cursor.fetchall()
    cursor.close()
    
    return render_template('admin/gerenciarUsuarios.html', usuarios=usuarios)


@admin.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso restrito.", "danger")
        return redirect(url_for('auth.login'))
    
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE id = %s", (id,))
    usuario = cursor.fetchone()
    if not usuario:
        flash("Usuário não encontrado.", "warning")
        cursor.close()
        return redirect(url_for('admin.gerenciar_usuarios'))
    
    if request.method == 'POST':
        nome      = request.form['nome']
        sexo      = request.form['sexo']
        cpf       = request.form['cpf']
        data_nasc = request.form['data_nasc']
        telefone  = request.form['telefone']
        pais      = request.form['pais']
        estado    = request.form['estado']
        cidade    = request.form['cidade']
        cep       = request.form['cep']
        email     = request.form['email']
        senha     = request.form.get('senha')  # pode ser vazio

        if senha:
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("""
                UPDATE usuario 
                SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                    pais=%s, estado=%s, cidade=%s, cep=%s, email=%s, senha=%s
                WHERE id=%s
            """, (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, cep, email, senha_hash, id))
        else:
            cursor.execute("""
                UPDATE usuario 
                SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                    pais=%s, estado=%s, cidade=%s, cep=%s, email=%s
                WHERE id=%s
            """, (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, cep, email, id))
        bd.commit()
        cursor.close()
        
        registrar_log(session['usuario_id'], "usuario", id, "editado", f"Usuário {nome} atualizado.")
        flash("Usuário atualizado com sucesso.", "success")
        return redirect(url_for('admin.home'))
    
    cursor.close()
    return render_template('admin/editarUsuario.html', usuario=usuario)


@admin.route('/excluir_usuario/<int:id>', methods=['POST'])
def excluir_usuario(id):
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso restrito.", "danger")
        return redirect(url_for('auth.login'))

    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT a.is_master FROM administrador a WHERE a.usuario_id = %s", (id,))
    admin_info = cursor.fetchone()
    cursor.close()

    if admin_info and admin_info.get('is_master'):
        flash("Não é possível excluir o administrador master.", "warning")
        return redirect(url_for('admin.gerenciar_usuarios'))

    cursor = bd.cursor()
    cursor.execute("DELETE FROM usuario WHERE id = %s", (id,))
    bd.commit()
    cursor.close()

    registrar_log(session['usuario_id'], "usuario", id, "excluído", "Usuário excluído pelo admin.")
    flash("Usuário excluído com sucesso!", "success")
    return redirect(url_for('admin.gerenciar_usuarios'))


# =====================================================
# Gerenciamento de Administradores
# (Admin Normal: visualizar; Admin Master: criar/editar/excluir)
# =====================================================
@admin.route('/gerenciar_adms')
def gerenciar_adms():
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso negado.", "danger")
        return redirect(url_for('auth.login'))
    
    cursor = bd.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id, u.nome, u.email, a.is_master
        FROM usuario u
        INNER JOIN administrador a ON u.id = a.usuario_id
    """)
    admins = cursor.fetchall()
    cursor.close()
    
    return render_template('admin/gerenciarAdministradores.html', admins=admins)


@admin.route('/novo_admin', methods=['POST'])
@requer_master  # Somente admin master pode criar novos administradores
def novo_admin():
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso restrito.", "danger")
        return redirect(url_for('auth.login'))
    
    try:
        nome      = request.form['nome']
        sexo      = request.form['sexo']
        data_nasc = request.form['data_nasc']
        pais      = request.form['pais']
        estado    = request.form['estado']
        cidade    = request.form['cidade']
        email     = request.form['email']
        senha     = request.form['senha']
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


# =====================================================
# Gerenciamento de Serviços
# (Ambos admin normal e master podem visualizar, editar e desativar serviços)
# =====================================================
@admin.route('/gerenciar_servicos')
def gerenciar_servicos():
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso negado.", "danger")
        return redirect(url_for('auth.login'))
    
    cursor = bd.cursor(dictionary=True)
    # A tabela de serviços está definida como "servicos" no seu banco de dados
    cursor.execute("SELECT * FROM servicos")
    servicos = cursor.fetchall()
    cursor.close()
    
    return render_template('admin/gerenciarServicos.html', servicos=servicos)


@admin.route('/editar_servico/<int:id>', methods=['GET', 'POST'])
def editar_servico(id):
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso negado.", "danger")
        return redirect(url_for('auth.login'))
    
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM servicos WHERE id = %s", (id,))
    servico = cursor.fetchone()
    if not servico:
        flash("Serviço não encontrado.", "warning")
        cursor.close()
        return redirect(url_for('admin.gerenciar_servicos'))
    
    if request.method == 'POST':
        # Atualiza informações do serviço; considere que "titulo" no banco corresponde a "nome" do serviço
        titulo    = request.form['nome']
        descricao = request.form['descricao']
        status    = request.form['status']  # 'ativo' ou 'inativo'
        
        cursor.execute("""
            UPDATE servicos 
            SET titulo=%s, descricao=%s, status=%s
            WHERE id=%s
        """, (titulo, descricao, status, id))
        bd.commit()
        cursor.close()
        registrar_log(session['usuario_id'], "servico", id, "editado", f"Serviço {titulo} atualizado.")
        flash("Serviço atualizado com sucesso.", "success")
        return redirect(url_for('admin.gerenciar_servicos'))
    
    cursor.close()
    return render_template('admin/editarServico.html', servico=servico)


@admin.route('/desativar_servico/<int:id>', methods=['POST'])
def desativar_servico(id):
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso negado.", "danger")
        return redirect(url_for('auth.login'))
    
    cursor = bd.cursor()
    cursor.execute("UPDATE servicos SET status='inativo' WHERE id=%s", (id,))
    bd.commit()
    cursor.close()
    registrar_log(session['usuario_id'], "servico", id, "desativado", f"Serviço ID {id} desativado.")
    flash("Serviço desativado com sucesso.", "success")
    return redirect(url_for('admin.gerenciar_servicos'))
