# app/utils.py
import os
import smtplib
from email.mime.text import MIMEText
from flask import current_app, url_for
from itsdangerous import URLSafeTimedSerializer

from functools import wraps
from flask import session, flash, redirect, url_for

def requer_master(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("is_master"):
            flash("Acesso restrito para administradores master.", "danger")
            return redirect(url_for('admin.home'))
        return func(*args, **kwargs)
    return wrapper



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
def enviar_email(destinatario, assunto, mensagem_html):
    """
    Função auxiliar para enviar e-mails.
    """
    remetente = os.environ.get("EMAIL_USER", "6tueeu6@gmail.com")
    senha_remetente = os.environ.get("EMAIL_PASSWORD", "izctformdfbzieot")
    
    mensagem = MIMEText(mensagem_html, 'html')
    mensagem["Subject"] = assunto
    mensagem["From"] = remetente
    mensagem["To"] = destinatario

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=60) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.ehlo()
            servidor.login(remetente, senha_remetente)
            servidor.send_message(mensagem)
        print(f"E-mail enviado para {destinatario} com sucesso!")
    except Exception as erro:
        print(f"Erro ao enviar e-mail para {destinatario}: {erro}")
def enviar_email_confirmacao(email):
    """
    Envia um e-mail de confirmação de cadastro para o usuário com um link único.
    """
    token = gerar_token_confirmacao(email)
    url_confirmacao = url_for('auth.confirmar_email', token=token, _external=True)
    
    html = f"""
    <html>
      <body>
        <p>Ola!!</p>
        <p>Recebemos seu cadastro e estamos quase lá!</p>
        <p>Para ativar sua conta, por favor confirme seu e-mail clicando no botão abaixo:</p>
        <p><a href="{url_confirmacao}">Confirmar E-mail</a></p>
        <p>Se você não realizou este cadastro, favor ignorar este e-mail.</p>
        <p>Obrigado(a) por se juntar a nós!</p>
        <p>Equipe Tu&Eu</p>
      </body>
    </html>
    """
    
    remetente = os.environ.get("EMAIL_USER", "6tueeu6@gmail.com")
    senha_remetente = os.environ.get("EMAIL_PASSWORD", "izctformdfbzieot")
    
    mensagem = MIMEText(html, 'html')
    mensagem["Subject"] = "Confirme seu e-mail para ativar sua conta - TU&EU"
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
        <p>Ola!!</p>
        <p>Recebemos uma solicitação para redefinir a sua senha.</p>
        <p>Se foi você quem solicitou, clique no botão abaixo para criar uma nova senha:/p>
        <p><a href="{reset_link}">Redefinir Senha</a></p>
        <p>Este link é válido por 1 hora e só pode ser usado uma vez.</p>
        <p>Se você não solicitou essa alteração, pode ignorar este e-mail com segurança. Sua senha atual continuará funcionando.</p>
        <p>Qualquer dúvida, estamos à disposição.</p>
        <p>Equipe Tu&Eu</p>
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

def enviar_email_reativacao(email, token):
    link = url_for('auth.reativar_conta', token=token, _external=True)
    assunto = "Reativação de Conta - Tu & Eu"
    mensagem = f"Olá,\n\nPara reativar sua conta, clique no link a seguir:\n\n{link}\n\nSe você não solicitou a reativação, ignore este e-mail."
    
    enviar_email(email, assunto, mensagem)

