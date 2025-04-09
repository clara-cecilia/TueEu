CREATE SCHEMA `cadastro_TueEu` ;

use cadastro_Tueeu;
  
CREATE TABLE `usuario` (
   `idUsuario` int NOT NULL AUTO_INCREMENT,
   `nome` varchar(100) NOT NULL,
   `sexo` varchar(10) NOT NULL,
   `cpf` varchar(14) DEFAULT NULL,
   `data_nasc` date NOT NULL,
   `telefone` varchar(11) DEFAULT NULL,
   `pais` varchar(20) NOT NULL,
   `estado` varchar(2) NOT NULL,
   `cidade` varchar(30) NOT NULL,
   `bairro` varchar(45) NOT NULL,
   `cep` varchar(8) DEFAULT NULL,
   `endereco` varchar(255) DEFAULT NULL,
   `email` varchar(105) NOT NULL,
   `senha` varchar(50) NOT NULL,
   PRIMARY KEY (`idUsuario`),
   UNIQUE KEY `email_unico` (`email`),
   UNIQUE KEY `cpf_unico` (`cpf`)
 ) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

select * from usuario;
