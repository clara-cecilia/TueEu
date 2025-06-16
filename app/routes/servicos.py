import os 
from flask import (
    Blueprint, request, session, flash, redirect,
    url_for, current_app, render_template
)
from flask import Flask
from config import Config
from app.models import bd, registrar_log
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)

servicos = Blueprint('servicos', __name__)

@servicos.route('/cadastrar_servico', methods=['GET', 'POST'])
def cadastrar_servico():
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para cadastrar um serviço.", "warning")
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Coleta os dados do formulário
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()  # Corrigido: sem acento
        categoria = request.form.get('categoria', '').strip()
        turnos = ",".join(request.form.getlist('turno'))  # Ex: "manha,tarde"
        tipo_servico = request.form.get('tipo_servico')  # 'oferece' ou 'busca'

        # Validação básica
        if not titulo or not descricao or not categoria or not tipo_servico:
            flash("Preencha todos os campos obrigatórios!", "danger")
            return redirect(url_for('servicos.cadastrar_servico'))

        try:
            cursor = bd.cursor()
            sql = """
                INSERT INTO servicos 
                (usuario_id, titulo, descricao, categoria, turnos, tipo_servico)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            valores = (
                session['usuario_id'], titulo, descricao, categoria,
                turnos, tipo_servico  # Já é 'oferece' ou 'busca'
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

        except Exception as e:
            bd.rollback()
            flash(f"Erro ao cadastrar serviço: {str(e)}", "danger")
            return redirect(url_for('servicos.cadastrar_servico'))

    # Renderiza o template (agora corrigido)
    return render_template('user/cadastrarServicos.html')


@servicos.route('/meus_servicos')
def meus_servicos():
    # Verifica se o usuário está logado
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para acessar seus serviços.", "warning")
        return redirect(url_for('auth.login'))

    cursor = bd.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM servicos 
        WHERE usuario_id = %s 
        ORDER BY criado_em DESC
    """, (session['usuario_id'],))
    servicos = cursor.fetchall()
    cursor.close()
    return render_template('user/meusServicos.html', servicos=servicos)   


@servicos.route('/editar_servico/<int:id>', methods=['GET', 'POST'])
def editar_servico(id):
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para editar um serviço.", "warning")
        return redirect(url_for('auth.login'))

    cursor = bd.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            # Coletar dados do formulário
            titulo = request.form['titulo']
            descricao = request.form['descricao']
            categoria = request.form['categoria']
            turnos = ",".join(request.form.getlist('turno'))
            tipo_servico = request.form['tipo_servico']
            
            # Atualizar no banco de dados
            cursor.execute("""
                UPDATE servicos 
                SET titulo = %s, 
                    descricao = %s, 
                    categoria = %s,
                    turnos = %s,
                    tipo_servico = %s,
                    status = 'ativo'
                WHERE id = %s AND usuario_id = %s
            """, (titulo, descricao, categoria, turnos, tipo_servico, id, session['usuario_id']))
            
            bd.commit()
            flash("Serviço atualizado com sucesso!", "success")
            return redirect(url_for('servicos.meus_servicos'))
            
        except Exception as e:
            bd.rollback()
            flash(f"Erro ao atualizar serviço: {str(e)}", "danger")
    
    # GET: Carregar dados do serviço
    cursor.execute("""
        SELECT *, 
               CASE WHEN turnos IS NULL THEN '' ELSE turnos END AS turnos_str
        FROM servicos 
        WHERE id = %s AND usuario_id = %s
    """, (id, session['usuario_id']))
    
    servico = cursor.fetchone()
    cursor.close()
    
    if not servico:
        flash("Serviço não encontrado.", "danger")
        return redirect(url_for('servicos.meus_servicos'))

    # Converter turnos para lista
    servico['turnos_lista'] = servico['turnos_str'].split(',') if servico['turnos_str'] else []
    
    return render_template('user/editarServicos.html', servico=servico)



@servicos.route('/excluir_servico/<int:id>', methods=['POST'])
def excluir_servico(id):
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para excluir um serviço.", "warning")
        return redirect(url_for('auth.login'))

    try:
        cursor = bd.cursor()
        # Verifica se o serviço pertence ao usuário antes de excluir
        cursor.execute("SELECT id FROM servicos WHERE id = %s AND usuario_id = %s", 
                      (id, session['usuario_id']))
        if not cursor.fetchone():
            flash("Serviço não encontrado ou não pertence a você.", "danger")
            return redirect(url_for('servicos.meus_servicos'))

        cursor.execute("DELETE FROM servicos WHERE id = %s", (id,))
        bd.commit()
        flash("Serviço excluído com sucesso!", "success")
    except Exception as e:
        bd.rollback()
        flash(f"Erro ao excluir serviço: {str(e)}", "danger")
    finally:
        cursor.close()

    return redirect(url_for('servicos.meus_servicos'))


@servicos.route('/desativar_servico/<int:id>', methods=['POST'])
def desativar_servico(id):
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para desativar um serviço.", "warning")
        return redirect(url_for('auth.login'))

    cursor = bd.cursor()
    cursor.execute(
        "UPDATE servicos SET status = 'inativo' WHERE id = %s AND usuario_id = %s", 
        (id, session['usuario_id'])
    )
    bd.commit()
    cursor.close()

    registrar_log(session['usuario_id'], "servico", id, "desativado", f"Serviço ID {id} foi desativado.")
    
    flash("Serviço desativado com sucesso!", "success")
    return redirect(url_for('servicos.meus_servicos'))
