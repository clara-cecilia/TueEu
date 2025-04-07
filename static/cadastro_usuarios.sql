CREATE SCHEMA `cadastro_TueEu` ;
use cadastro_Tueeu;
CREATE TABLE `cadastro_tueeu`.`usuario` (
  `idUsuario` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(100) NOT NULL,
  `sexo` VARCHAR(10) NOT NULL,
  `cpf` INT NOT NULL,
  `data_nasc` DATE NOT NULL,
  `telefone` INT NOT NULL,
  `pais` VARCHAR(20) NOT NULL,
  `estado` VARCHAR(2) NOT NULL,
  `cidade` VARCHAR(30) NOT NULL,
  `bairro` VARCHAR(45) NOT NULL,
  `cep` INT NOT NULL,
  `endereço` VARCHAR(255) NOT NULL,
  `email` VARCHAR(105) NOT NULL,
  `senha` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`idUsuario`));
  
  ALTER TABLE usuario
MODIFY COLUMN cpf VARCHAR(11),
MODIFY COLUMN telefone VARCHAR(11),
MODIFY COLUMN cep VARCHAR(8);

select * from usuario;

