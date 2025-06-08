# app/utils.py
import os
import smtplib
from email.mime.text import MIMEText
from flask import current_app, url_for
from itsdangerous import URLSafeTimedSerializer

# ===== Geração de Tokens =====
def gerar_token_confirmacao(email):
    """
    Gera um token seguro para confirmação de e-mail.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='confirmacao-email-salt')

def gerar_token_reset(email):
    """
    Gera um token seguro para redefinição de senha.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='reset-password-salt')

# ===== Envio de E-mails =====
def enviar_email_confirmacao(email):
    """
    Envia um e-mail de confirmação de cadastro para o usuário com um link único.
    """
    token = gerar_token_confirmacao(email)
    url_confirmacao = url_for('auth.confirmar_email', token=token, _external=True)
    
    html = f"""
    <html>
      <body>
        <p>Para confirmar seu cadastro, clique no link abaixo:</p>
        <p><a href="{url_confirmacao}">Confirmar E-mail</a></p>
      </body>
    </html>
    """
    
    remetente = os.environ.get("EMAIL_USER", "6tueeu6@gmail.com")
    senha_remetente = os.environ.get("EMAIL_PASSWORD", "izctformdfbzieot")
    
    mensagem = MIMEText(html, 'html')
    mensagem["Subject"] = "Confirmação de Cadastro"
    mensagem["From"] = remetente
    mensagem["To"] = email
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=60) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.ehlo()
            servidor.login(remetente, senha_remetente)
            servidor.send_message(mensagem)
        print(f"E-mail de confirmação enviado para {email} com sucesso!")
    except Exception as erro:
        print(f"Erro ao enviar e-mail de confirmação: {erro}")

def enviar_email_reset(email):
    """
    Envia um e-mail com link para redefinição de senha.
    """
    token = gerar_token_reset(email)
    reset_link = url_for('auth.confirmar_reset', token=token, _external=True)
    
    html = f"""
    <html>
      <body>
        <p>Para redefinir sua senha, clique no link abaixo:</p>
        <p><a href="{reset_link}">Redefinir Senha</a></p>
        <p>Este link expira em 1 hora.</p>
      </body>
    </html>
    """
    
    remetente = os.environ.get("EMAIL_USER", "6tueeu6@gmail.com")
    senha_remetente = os.environ.get("EMAIL_PASSWORD", "izctformdfbzieot")
    
    mensagem = MIMEText(html, 'html')
    mensagem["Subject"] = "Redefinição de Senha"
    mensagem["From"] = remetente
    mensagem["To"] = email
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=60) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.ehlo()
            servidor.login(remetente, senha_remetente)
            servidor.send_message(mensagem)
        print(f"E-mail de redefinição enviado para {email} com sucesso!")
    except Exception as erro:
        print(f"Erro ao enviar e-mail de redefinição: {erro}")
