import os
from flask import (
    Blueprint, request, session, flash, redirect,
    url_for, current_app, render_template
)
from app.models import bd, registrar_log

servicos = Blueprint('servicos', __name__)

@servicos.route('/cadastrar_servicos', methods=['GET', 'POST'])
def cadastrar_servico():
    # Verifica se o usuário está logado
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para cadastrar um serviço.", "warning")
        return redirect(url_for('auth.login'))
    
    # Processamento do formulário de cadastro
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        estado = request.form['estado']
        cidade = request.form['cidade']
        turnos = ",".join(request.form.getlist('turno'))
        servicos_interesse = ",".join(request.form.getlist('servicos_interesse'))
        imagem = request.files.get('imagem')

        imagem_path = None
        if imagem and imagem.filename != '':
            upload_folder = current_app.config['UPLOAD_FOLDER']
            # Cria o diretório se ele não existir
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            imagem_path = os.path.join(upload_folder, imagem.filename)
            imagem.save(imagem_path)

        cursor = bd.cursor()
        sql = """
            INSERT INTO servicos 
            (usuario_id, titulo, descricao, categoria, estado, cidade, turnos, servicos_interesse, imagem)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            session['usuario_id'], titulo, descricao, categoria,
            estado, cidade, turnos, servicos_interesse, imagem_path
        )
        cursor.execute(sql, valores)
        bd.commit()
        servico_id = cursor.lastrowid
        cursor.close()

        registrar_log(
            session['usuario_id'], "servico", servico_id, 
            "criado", f"Serviço '{titulo}' cadastrado."
        )
        flash("Serviço cadastrado com sucesso!", "success")
        return redirect(url_for('servicos.meus_servicos'))

    # Template localizado na subpasta 'user'
    return render_template('user/cadastrarServicos.html')


@servicos.route('/meus_servicos')
def meus_servicos():
    # Verifica se o usuário está logado
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para acessar seus serviços.", "warning")
        return redirect(url_for('auth.login'))

    cursor = bd.cursor(dictionary=True)
    cursor.execute("SELECT * FROM servicos WHERE usuario_id = %s", (session['usuario_id'],))
    servicos_list = cursor.fetchall()
    cursor.close()

    return render_template('user/meusServicos.html', servicos=servicos_list)


@servicos.route('/editar_servico/<int:id>', methods=['GET', 'POST'])
def editar_servico(id):
    # Verifica se o usuário está logado
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para editar um serviço.", "warning")
        return redirect(url_for('auth.login'))

    cursor = bd.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM servicos WHERE id = %s AND usuario_id = %s", 
        (id, session['usuario_id'])
    )
    servico = cursor.fetchone()

    if not servico:
        flash("Serviço não encontrado ou não pertence a você.", "warning")
        cursor.close()
        return redirect(url_for('servicos.meus_servicos'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        estado = request.form['estado']
        cidade = request.form['cidade']
        turnos = ",".join(request.form.getlist('turno'))
        servicos_interesse = ",".join(request.form.getlist('servicos_interesse'))

        cursor.execute("""
            UPDATE servicos 
            SET titulo = %s, descricao = %s, categoria = %s, estado = %s, cidade = %s, 
                turnos = %s, servicos_interesse = %s 
            WHERE id = %s AND usuario_id = %s
        """, (titulo, descricao, categoria, estado, cidade, turnos, servicos_interesse, id, session['usuario_id']))
        bd.commit()
        cursor.close()

        registrar_log(
            session['usuario_id'], "servico", id, 
            "editado", f"Serviço '{titulo}' atualizado."
        )
        flash("Serviço atualizado com sucesso!", "success")
        return redirect(url_for('servicos.meus_servicos'))

    cursor.close()
    # Corrigido o caminho: o template de edição está na subpasta 'user'
    return render_template('user/editarServico.html', servico=servico)


@servicos.route('/excluir_servico/<int:id>')
def excluir_servico(id):
    # Verifica se o usuário está logado
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para excluir um serviço.", "warning")
        return redirect(url_for('auth.login'))

    cursor = bd.cursor()
    cursor.execute(
        "DELETE FROM servicos WHERE id = %s AND usuario_id = %s", 
        (id, session['usuario_id'])
    )
    bd.commit()
    cursor.close()

    registrar_log(
        session['usuario_id'], "servico", id, 
        "excluído", "Serviço excluído pelo usuário."
    )
    flash("Serviço excluído com sucesso!", "success")
    return redirect(url_for('servicos.meus_servicos'))
