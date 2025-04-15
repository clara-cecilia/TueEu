import hashlib
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import mysql.connector

# Função para gerar um hash único
def generate_reset_code(email):
    salt = os.urandom(16)  # Gera um salt aleatório
    timestamp = datetime.now().isoformat()  # Adiciona um timestamp
    data = f"{email}{timestamp}{salt}".encode('utf-8')
    reset_code = hashlib.sha256(data).hexdigest()
    return reset_code

# Função para salvar o código de redefinição no banco de dados
def store_reset_code_in_db(email, reset_code):
    conn = mysql.connector.connect(
        host="localhost",  # Substitua pelo seu host
        user="root",  # Substitua pelo seu usuário
        password="senha",  # Substitua pela sua senha
        database="cadastro_tueeu"  # Substitua pelo seu banco de dados
    )

    cursor = conn.cursor()

    # Definir a data de expiração (por exemplo, 1 hora)
    expiration_time = datetime.now() + timedelta(hours=1)

    # Atualizar ou inserir o código e a data de expiração na tabela de usuário
    cursor.execute("""
        UPDATE usuario
        SET reset_code = %s, reset_code_expiration = %s
        WHERE email = %s
    """, (reset_code, expiration_time, email))

    conn.commit()
    cursor.close()
    conn.close()

# Função para enviar o código por e-mail
def send_reset_email(email, reset_code):
    sender_email = "seu_email@gmail.com"
    sender_password = "sua_senha"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    subject = "Redefinição de Senha"
    body = f"Use o seguinte código para redefinir sua senha: {reset_code}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# Função para verificar se o código de redefinição é válido
def verify_reset_code(email, reset_code):
    conn = mysql.connector.connect(
        host="localhost",  # Substitua pelo seu host
        user="root",  # Substitua pelo seu usuário
        password="senha",  # Substitua pela sua senha
        database="cadastro_tueeu"  # Substitua pelo seu banco de dados
    )

    cursor = conn.cursor()

    # Consultar o código e a data de expiração do banco
    cursor.execute("""
        SELECT reset_code, reset_code_expiration 
        FROM usuario 
        WHERE email = %s
    """, (email,))
    result = cursor.fetchone()

    conn.close()

    if result:
        stored_reset_code, expiration_time = result
        # Verificar se o código é válido e não expirou
        if stored_reset_code == reset_code and datetime.now() < expiration_time:
            return True
        else:
            return False
    else:
        return False
    
# Função para redefinir a senha
def reset_password(email, new_password):
    conn = mysql.connector.connect(
        host="localhost",  # Substitua pelo seu host
        user="root",  # Substitua pelo seu usuário
        password="senha",  # Substitua pela sua senha
        database="cadastro_tueeu"  # Substitua pelo seu banco de dados
    )

    cursor = conn.cursor()

    # Atualizar a senha no banco de dados
    cursor.execute("""
        UPDATE usuario 
        SET senha = %s, reset_code = NULL, reset_code_expiration = NULL 
        WHERE email = %s
    """, (new_password, email))

    conn.commit()
    cursor.close()
    conn.close()

    print("Senha redefinida com sucesso!")

# Exemplo de uso
if __name__ == "__main__":
    user_email = input("Digite o e-mail do usuário: ")
    reset_code = generate_reset_code(user_email)
    store_reset_code_in_db(user_email, reset_code)
    send_reset_email(user_email, reset_code)
    print(f"Código de redefinição gerado e enviado por e-mail: {reset_code}")