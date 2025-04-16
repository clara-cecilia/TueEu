import hashlib
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import mysql.connector

def generate_reset_code(email):
    salt = os.urandom(16)
    timestamp = datetime.now().isoformat()
    data = f"{email}{timestamp}{salt}".encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def store_reset_code_in_db(email, reset_code):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="senha",
        database="cadastro_tueeu"
    )
    cursor = conn.cursor()
    expiration = datetime.now() + timedelta(hours=1)
    cursor.execute("""
        UPDATE usuario
        SET reset_code = %s, reset_code_expiration = %s
        WHERE email = %s
    """, (reset_code, expiration, email))
    conn.commit()
    cursor.close()
    conn.close()

def send_reset_email(email, reset_code):
    sender_email = "seu_email@gmail.com"
    sender_password = "sua_senha"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    body = f"Seu código de redefinição de senha é: {reset_code}"

    msg = MIMEText(body)
    msg['Subject'] = "Redefinição de Senha"
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

def verify_reset_code(email, reset_code):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="senha",
        database="cadastro_tueeu"
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reset_code, reset_code_expiration 
        FROM usuario 
        WHERE email = %s
    """, (email,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_code, expiration = result
        if stored_code == reset_code and datetime.now() < expiration:
            return True
    return False

def reset_password(email, new_password):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="senha",
        database="cadastro_tueeu"
    )
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE usuario 
        SET senha = %s, reset_code = NULL, reset_code_expiration = NULL 
        WHERE email = %s
    """, (new_password, email))
    conn.commit()
    cursor.close()
    conn.close()
