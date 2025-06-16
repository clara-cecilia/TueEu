# app/routes/admin.py
from flask import (
    Blueprint, request, session, flash,
    redirect, url_for, current_app, render_template
)
import bcrypt
from app.models import bd, registrar_log
from app.utils import requer_master  # decorador definido em utils.py
from app.utils import enviar_email_confirmacao

from bcrypt import hashpw, gensalt 
import os

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
        status    = request.form['status']  # novo campo para o status
        senha     = request.form.get('senha')  # pode ser vazio

        if senha:
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("""
                UPDATE usuario 
                SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                    pais=%s, estado=%s, cidade=%s, cep=%s, email=%s, senha=%s, status=%s
                WHERE id=%s
            """, (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, cep, email, senha_hash, status, id))
        else:
            cursor.execute("""
                UPDATE usuario 
                SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                    pais=%s, estado=%s, cidade=%s, cep=%s, email=%s, status=%s 
                WHERE id=%s
            """, (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, cep, email, status, id))
        bd.commit()
        registrar_log(session['usuario_id'], "usuario", id, "editado", f"Usuário {nome} atualizado.")
        cursor.close()
        flash("Usuário atualizado com sucesso.", "success")
        return redirect(url_for('admin.home'))
    
    # Para o método GET, buscamos os serviços anunciados por esse usuário:
    cursor.execute("SELECT * FROM servicos WHERE usuario_id = %s", (id,))
    servicos = cursor.fetchall()
    cursor.close()
    
    # Passando também a variável 'servicos' para o template
    return render_template('admin/editarUsuario.html', usuario=usuario, servicos=servicos)

@admin.route('/desativar_usuario/<int:id>', methods=['POST'])
def desativar_usuario(id):
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso restrito.", "danger")
        return redirect(url_for('auth.login'))

    cursor = bd.cursor()
    cursor.execute("UPDATE usuario SET status='inativo' WHERE id=%s", (id,))
    bd.commit()
    cursor.close()

    registrar_log(session['usuario_id'], "usuario", id, "desativado", "Usuário desativado pelo admin.")
    flash("Usuário desativado com sucesso!", "success")
    return redirect(url_for('admin.gerenciar_usuarios'))

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
        SELECT u.id, u.nome, u.email, u.status, a.is_master 
        FROM usuario u
        INNER JOIN administrador a ON u.id = a.usuario_id
    """)
    admins = cursor.fetchall()
    cursor.close()
    
    return render_template('admin/gerenciarAdmin.html', admins=admins)


@admin.route('/novo_admin', methods=['POST'])
@requer_master  # Somente admin master pode criar novos administradores
def novo_admin():
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso restrito.", "danger")
        return redirect(url_for('auth.login'))
    
    try:
        # Dados do novo administrador
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
        
        # Registrar log
        registrar_log(session['usuario_id'], "administrador", novo_usuario_id, "criado", f"Administrador {nome} cadastrado.")
        
        # Gerar token para confirmação de e-mail
        from itsdangerous import URLSafeTimedSerializer
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps(email, salt='confirmacao-email-salt')
        
        # Envia o e-mail de confirmação
        enviar_email_confirmacao(email)
        
        flash("Administrador cadastrado com sucesso! Um e-mail de confirmação foi enviado.", "success")
        
    except Exception as erro:
        flash("Erro ao cadastrar administrador: " + str(erro), "danger")
    
    return redirect(url_for('admin.gerenciar_adms'))

@admin.route('/editar_admin/<int:id>', methods=['GET', 'POST'])
@requer_master  # Somente admin master pode editar administradores
def editar_admin(id):
    # Verifica acesso
    if 'usuario_email' not in session or not session.get('is_admin'):
        flash("Acesso restrito.", "danger")
        return redirect(url_for('auth.login'))
    
    cursor = bd.cursor(dictionary=True)
    # Busque os dados do usuário que é administrador
    cursor.execute("SELECT u.id, u.nome, u.email, u.sexo, u.cpf, u.data_nasc, u.telefone, u.pais, u.estado, u.cidade, u.cep, u.status FROM usuario u WHERE u.id = %s", (id,))
    usuario = cursor.fetchone()
    if not usuario:
        flash("Administrador não encontrado.", "warning")
        cursor.close()
        return redirect(url_for('admin.gerenciar_adms'))
    
    # Buscando informações específicas do administrador, como se ele é master ou não:
    cursor.execute("SELECT is_master FROM administrador WHERE usuario_id = %s", (id,))
    admin_info = cursor.fetchone()
    if not admin_info:
        flash("Informação administrativa não encontrada.", "warning")
        cursor.close()
        return redirect(url_for('admin.gerenciar_adms'))
    
    if request.method == 'POST':
        # Atualiza os dados básicos do usuário que também é administrador
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
        status    = request.form['status']  # novo campo para o status
        senha     = request.form.get('senha')  # campo opcional

        if senha:
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("""
                UPDATE usuario 
                SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                    pais=%s, estado=%s, cidade=%s, cep=%s, email=%s, senha=%s, status=%s
                WHERE id=%s
            """, (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, cep, email, senha_hash,status, id))
        else:
            cursor.execute("""
                UPDATE usuario 
                SET nome=%s, sexo=%s, cpf=%s, data_nasc=%s, telefone=%s,
                    pais=%s, estado=%s, cidade=%s, cep=%s, email=%s, status=%s
                WHERE id=%s
            """, (nome, sexo, cpf, data_nasc, telefone, pais, estado, cidade, cep, email, status, id))
        bd.commit()
        cursor.close()
        registrar_log(session['usuario_id'], "administrador", id, "editado", f"Administrador {nome} atualizado.")
        flash("Administrador atualizado com sucesso.", "success")
        return redirect(url_for('admin.gerenciar_adms'))
    
    cursor.close()
    # Renderize o template passando dados do usuário e do administrador
    return render_template('admin/editarAdmin.html', usuario=usuario, admin_info=admin_info)



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
        # Obtenha os valores dos campos do formulário
        titulo             = request.form['nome']
        descricao          = request.form['descricao']
        categoria          = request.form['categoria']
        estado             = request.form['estado']
        cidade             = request.form['cidade']
        turnos             = request.form.getlist('turnos')  # seleção múltipla
        servicos_interesse = request.form.getlist('servicos_interesse')  # seleção múltipla
        status             = request.form['status']  # 'ativo' ou 'inativo'
        
        # Tratamento para os campos que são do tipo SET (MySQL espera uma string separada por vírgulas)
        turnos_str = ','.join(turnos)
        servicos_interesse_str = ','.join(servicos_interesse)
        
        # Tratar o upload de imagem se for enviado; caso contrário, manter a imagem atual
        imagem_file = request.files.get('imagem')
        imagem_path = servico.get('imagem')  # valor atual
        if imagem_file and imagem_file.filename != '':
            upload_folder = current_app.config['UPLOAD_FOLDER']
            # Cria a pasta se não existir
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            imagem_path = os.path.join(upload_folder, imagem_file.filename)
            imagem_file.save(imagem_path)
        
        # Agora, atualize todos os campos na tabela
        cursor.execute("""
            UPDATE servicos 
            SET titulo = %s, descricao = %s, categoria = %s, estado = %s, cidade = %s,
                turnos = %s, servicos_interesse = %s, imagem = %s, status = %s
            WHERE id = %s
        """, (titulo, descricao, categoria, estado, cidade, turnos_str, servicos_interesse_str, imagem_path, status, id))
        bd.commit()
        registrar_log(session['usuario_id'], "servico", id, "editado", f"Serviço {titulo} atualizado.")
        cursor.close()
        flash("Serviço atualizado com sucesso.", "success")
        return redirect(url_for('admin.gerenciar_servicos'))
    
    # Para o GET, além dos dados do serviço, você pode enviar listas com os valores possíveis para campos ENUM/SET:
    # Exemplo: categorias, turnos, servicos_interesse, status (caso queira forçar a validacão no template)
    categorias = [
        'Estética', 'Automotiva', 'Limpeza Domiciliar', 'Mecânica', 'Informática',
        'Jardinagem', 'Reformas / Manutenção', 'Educação', 'Artes e Cultura',
        'Eventos', 'Transporte', 'Saúde e Bem-estar', 'Consultoria'
    ]
    turnos_possiveis = ['Manhã', 'Tarde', 'Noite']
    servicos_interesse_possiveis = [
        'Estética', 'Automotiva', 'Limpeza Domiciliar', 'Mecânica', 'Informática',
        'Jardinagem', 'Reformas / Manutenção', 'Educação', 'Artes e Cultura',
        'Eventos', 'Transporte', 'Saúde e Bem-estar', 'Consultoria'
    ]
    status_opcoes = ['ativo', 'inativo']
    
    # Também busque os dados do usuário associado, se necessário
    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT id, email, status FROM usuario WHERE id = %s", (servico['usuario_id'],))
    usuario = cursor.fetchone()
    cursor.close()
    
    return render_template('admin/editarServico.html', servico=servico, usuario=usuario,
                           categorias=categorias, turnos_possiveis=turnos_possiveis,
                           servicos_interesse_possiveis=servicos_interesse_possiveis, 
                           status_opcoes=status_opcoes)

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
