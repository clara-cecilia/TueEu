import random
import smtplib
from email.mime.text import MIMEText
from bcrypt import hashpw, gensalt
from datetime import datetime, timedelta
import mysql.connector

# Configuração da conexão com o banco
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="280697",
    port='3306',
    database="cadastro_tueeu"
)

def generate_reset_code(email)  :
    return str(random.randint(100000, 999999))

def store_reset_code_in_db(email, code):
    cursor = db.cursor()
    cursor.execute("DELETE FROM reset_senhas WHERE email = %s", (email,))
    cursor.execute(
        "INSERT INTO reset_senhas (email, codigo, expiracao) VALUES (%s, %s, %s)",
        (email, code, datetime.now() + timedelta(minutes=10))
    )
    db.commit()
    cursor.close()

def send_reset_email(email, code):
    remetente = "seuemail@gmail.com"
    senha_email = "sua_senha"

    msg = MIMEText(f"Seu código de recuperação é: {code}")
    msg["Subject"] = "Recuperação de senha"
    msg["From"] = remetente
    msg["To"] = email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(remetente, senha_email)
            servidor.send_message(msg)
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

def verify_reset_code(email, code):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reset_senhas WHERE email = %s AND codigo = %s", (email, code))
    resultado = cursor.fetchone()
    cursor.close()
    if resultado and resultado["expiracao"] > datetime.now():
        return True
    return False

def reset_password(email, nova_senha):
    nova_senha_hash = hashpw(nova_senha.encode('utf-8'), gensalt()).decode('utf-8')
    cursor = db.cursor()
    cursor.execute("UPDATE usuario SET senha = %s WHERE email = %s", (nova_senha_hash, email))
    db.commit()
    cursor.execute("DELETE FROM reset_senhas WHERE email = %s", (email,))
    db.commit()
    cursor.close()

def gerar_codigo():
    return str(random.randint(100000, 999999))

def enviar_email(destinatario, codigo):
    remetente = "seuemail@gmail.com"
    senha = "sua_senha_de_app"  # Use senha de aplicativo para Gmail

    corpo = f"Seu código de redefinição de senha é: {codigo}"

    msg = MIMEText(corpo)
    msg["Subject"] = "Código de Redefinição de Senha"
    msg["From"] = remetente
    msg["To"] = destinatario

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(remetente, senha)
            servidor.sendmail(remetente, destinatario, msg.as_string())
        return True
    except Exception as e:
        print("Erro ao enviar e-mail:", e)
        return False
