USE cadastro_tueeu;

CREATE TABLE usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    sexo ENUM('Masculino', 'Feminino') NOT NULL,
    cpf CHAR(11) NOT NULL UNIQUE,
    data_nasc DATE NOT NULL,
    telefone CHAR(11),
    pais VARCHAR(50) NOT NULL,
    estado CHAR(2) NOT NULL,
    cidade VARCHAR(50) NOT NULL,
    bairro VARCHAR(50) NOT NULL,
    cep CHAR(8) NOT NULL,
    endereco VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL
);

ALTER TABLE usuario 
ADD is_admin TINYINT DEFAULT 0;
ADD reset_code VARCHAR(64),
ADD reset_code_expiration DATETIME;

