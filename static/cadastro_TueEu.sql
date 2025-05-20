CREATE SCHEMA `cadastro_TueEu`;
USE cadastro_TueEu;
select * from usuario;
CREATE TABLE usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    sexo ENUM('Masculino', 'Feminino') NOT NULL,
    cpf VARCHAR(14) UNIQUE DEFAULT NULL,
    data_nasc DATE NOT NULL,
    telefone VARCHAR(11) DEFAULT NULL,
    pais VARCHAR(50) NOT NULL,
    estado CHAR(2) NOT NULL,
    cidade VARCHAR(50) NOT NULL,
    bairro VARCHAR(50) NOT NULL,
    cep CHAR(8) DEFAULT NULL,
    endereco VARCHAR(255) DEFAULT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    is_admin TINYINT DEFAULT 0,
    reset_code VARCHAR(64) DEFAULT NULL,
    reset_code_expiration DATETIME DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE reset_senhas (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    email VARCHAR(255) NOT NULL,
    codigo VARCHAR(10) NOT NULL,
    expiracao DATETIME NOT NULL,
    FOREIGN KEY (email) REFERENCES usuario(email) ON DELETE CASCADE
);
