-- Criar schema se não existir
CREATE SCHEMA IF NOT EXISTS `cadastro_tueEu`;
USE `cadastro_tueEu`;

-- Tabela de Usuários
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
    cep CHAR(8) DEFAULT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    status ENUM('ativo', 'inativo') DEFAULT 'ativo',
    email_verificado TINYINT DEFAULT 0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela de Administradores
CREATE TABLE administrador (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    is_master TINYINT DEFAULT 0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela de Serviços (com tipo_servico e sem cidade/estado)
CREATE TABLE servicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    turnos VARCHAR(100), -- armazenar 'Manhã,Tarde' por exemplo
    tipo_servico ENUM('oferece', 'busca') NOT NULL DEFAULT 'oferece', -- novo campo
    status ENUM('ativo', 'inativo') DEFAULT 'ativo',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela de Logs (registro de ações administrativas)
CREATE TABLE logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT DEFAULT NULL, -- Quem fez a ação (permite NULL)
    entidade ENUM('usuario', 'administrador', 'servico') NOT NULL,
    entidade_id INT NOT NULL, -- ID da entidade afetada
    acao ENUM('criado', 'editado', 'ativado', 'desativado', 'excluído', 'login', 'email confirmado') NOT NULL,
    detalhes TEXT DEFAULT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
