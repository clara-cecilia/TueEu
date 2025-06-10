#criar codigo do BD static>cadastro_Tu&eu

#cria adm master
from werkzeug.security import generate_password_hash

def criar_administrador_master():
    try:
        cursor = bd.cursor(dictionary=True)

        # Verifica se já existe o admin master
        cursor.execute("SELECT * FROM usuario WHERE email = %s", ("master@tueeu.com.br",))
        existe = cursor.fetchone()

        if not existe:
            senha_hash = $2b$12$Mt74BfQhLiBtm8VmELuO6OB93.fpopVdrDjP3mej3bdNMtc0IpJb6 //1234

            # Preenche todos os campos obrigatórios, incluindo o bairro
            cursor.execute("""
                INSERT INTO usuario (
                    nome, telefone, email, cpf, endereco, senha,
                    data_nasc, pais, estado, cidade, bairro
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                "Administrador Master",     # nome
                "0000000000",               # telefone
                "master@tueeu.com.br",      # email
                "00000000001",              # cpf
                "Sistema",                  # endereco
                senha_hash,                 # senha (hash)
                "2025-06-01",               # data_nasc
                "Brasil",                   # pais
                "DF",                       # estado
                "Brasília",                 # cidade
                "Plano Piloto"              # bairro
            ))
            bd.commit()

            usuario_id = cursor.lastrowid

            # Insere o administrador como master
            cursor.execute("""
                INSERT INTO administrador (usuario_id, is_master)
                VALUES (%s, %s)
            """, (usuario_id, True))
            bd.commit()

            print("Administrador master criado com sucesso!")
        else:
            print("Administrador master já existe.")

        cursor.close()
    except Exception as e:
        print(f"Erro ao criar administrador master: {e}")

criar_administrador_master()
