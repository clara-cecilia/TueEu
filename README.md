# 🌐 Tu&Eu

Sistema web desenvolvido com Flask, que permite o cadastro, login, confirmação de e-mail e recuperação de senha de usuários. Oferece interface diferenciada para administradores e usuários comuns.

## 🚀 Funcionalidades

- Cadastro de usuários com verificação de e-mail (double opt-in)
- Login com criptografia de senha (bcrypt)
- Recuperação de senha por e-mail
- Edição de dados pessoais
- Sessão segura com controle de acesso
- Diferenciação de perfis (admin / usuário comum)
- Painel personalizado após login

## 🛠️ Tecnologias utilizadas

- [Flask](https://flask.palletsprojects.com/)
- MySQL (via `mysql-connector-python`)
- [bcrypt](https://pypi.org/project/bcrypt/)
- [itsdangerous](https://pythonhosted.org/itsdangerous/)
- Bootstrap (no front-end)
- SMTP com Gmail (envio de e-mails)

## 📁 Estrutura de pastas

📌 Observações:
Flask: framework web principal.

mysql-connector-python: conexão com banco de dados MySQL.

bcrypt: criptografia de senhas.

itsdangerous: geração de tokens seguros (útil para reset de senha).

python-dotenv: leitura do arquivo .env para carregar variáveis de ambiente.

email-validator: (opcional, mas recomendado) para validar e-mails de forma segura.
