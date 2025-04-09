import os
import hashlib

# Função para gerar o hash com salt
def gerar_hash_salt(senha: str):
    # Gerar um salt aleatório de 16 bytes
    salt = os.urandom(16)
    
    # Concatenar a senha com o salt e gerar o hash
    senha_com_salt = senha.encode('utf-8') + salt
    hash_senha = hashlib.sha256(senha_com_salt).hexdigest()
    
    # Retornar o hash da senha e o salt (vamos salvar ambos no banco de dados)
    return hash_senha, salt

# Exemplo de uso
senha = "minha_senha_segura"
hash_senha, salt = gerar_hash_salt(senha)

print(f"Hash da senha: {hash_senha}")
print(f"Salt: {salt.hex()}")

def registrar_usuario(username, senha):
    hash_senha, salt = gerar_hash_salt(senha)
    cursor.execute('INSERT INTO usuarios (username, senha_hash, salt) VALUES (?, ?, ?)', 
                   (username, hash_senha, salt.hex()))
    conn.commit()
# Função para registrar um novo usuário
# Exemplo de registro
registrar_usuario("usuario_teste", "minha_senha_segura")

# Fechar a conexão
conn.close()