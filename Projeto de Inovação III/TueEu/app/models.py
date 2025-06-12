# app/models.py
import os
import mysql.connector  # Certifique-se de que este módulo esteja instalado

def conectar_bd():
    """Estabelece conexão com o banco de dados usando credenciais seguras."""
    try:
        conexao = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME")
        )
        print("✅ Conexão realizada com sucesso!")
        return conexao
    except mysql.connector.Error as erro:
        print(f"❌ Erro na conexão: {erro}")
        return None

# Conexão que será compartilhada com os demais módulos
bd = conectar_bd()

def registrar_log(id_usuario, entidade, id_entidade, acao, detalhes=None):
    """
    Registra um log de ação de usuário no banco de dados.
    
    Parâmetros:
      - id_usuario: ID do usuário que realizou a ação.
      - entidade: Nome da entidade afetada.
      - id_entidade: ID da entidade afetada.
      - acao: Ação realizada (permitido: 'criado', 'editado', 'ativado', 'desativado', 'excluído', 'login', 'email confirmado').
      - detalhes: Informações adicionais (opcional).
    """
    acoes_permitidas = ['criado', 'editado', 'ativado', 'desativado', 'excluído', 'login', 'email confirmado']
    if acao not in acoes_permitidas:
        print(f"Erro: '{acao}' não é um valor permitido para a coluna 'acao'.")
        return

    try:
        cursor = bd.cursor()
        comando_sql = (
            "INSERT INTO logs (usuario_id, entidade, entidade_id, acao, detalhes) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        cursor.execute(comando_sql, (id_usuario, entidade, id_entidade, acao, detalhes))
        bd.commit()
        cursor.close()
    except mysql.connector.Error as erro:
        print(f"Erro ao registrar log: {erro}")
