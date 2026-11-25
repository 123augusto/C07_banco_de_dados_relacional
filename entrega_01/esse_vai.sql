CREATE SCHEMA IF NOT EXISTS `festival_inovacao`;
USE `festival_inovacao`;

-- 1. Tabela Raiz
CREATE TABLE `pessoa` (
  `id_pessoa` INT AUTO_INCREMENT PRIMARY KEY,
  `nome` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) UNIQUE NOT NULL,
  `telefone` VARCHAR(15)
);

-- 2. Subclasses (Herança 1:1)
CREATE TABLE `palestrante` (
  `id_pessoa` INT PRIMARY KEY,
  `minicurriculo` VARCHAR(255),
  `area_especialidade` VARCHAR(50),
  CONSTRAINT `fk_pal_pes` FOREIGN KEY (`id_pessoa`) REFERENCES `pessoa` (`id_pessoa`)
);

CREATE TABLE `participante` (
  `id_pessoa` INT PRIMARY KEY,
  `tipo_ingresso` VARCHAR(20) NOT NULL,
  CONSTRAINT `fk_par_pes` FOREIGN KEY (`id_pessoa`) REFERENCES `pessoa` (`id_pessoa`)
);

-- 3. Entidade 1:1 com Participante
CREATE TABLE `credencial` (
  `id_credencial` INT AUTO_INCREMENT PRIMARY KEY,
  `codigo` VARCHAR(20) UNIQUE NOT NULL,
  `id_participante` INT UNIQUE NOT NULL,
  CONSTRAINT `fk_cred_par` FOREIGN KEY (`id_participante`) REFERENCES `participante` (`id_pessoa`)
);

-- 4. Infraestrutura
CREATE TABLE `espaco` (
  `id_espaco` INT AUTO_INCREMENT PRIMARY KEY,
  `nome_local` VARCHAR(50) NOT NULL,
  `capacidade_maxima` INT NOT NULL
);

-- 5. Atividade (Com Recursividade)
CREATE TABLE `atividade` (
  `id_atividade` INT AUTO_INCREMENT PRIMARY KEY,
  `titulo` VARCHAR(150) NOT NULL,
  `descricao` VARCHAR(255),
  `duracao_minutos` INT,
  `data_hora_inicio` DATETIME NOT NULL,
  `id_espaco` INT,
  `id_palestrante` INT,
  `id_atividade_prerequisito` INT,
  CONSTRAINT `fk_ati_esp` FOREIGN KEY (`id_espaco`) REFERENCES `espaco` (`id_espaco`),
  CONSTRAINT `fk_ati_pal` FOREIGN KEY (`id_palestrante`) REFERENCES `palestrante` (`id_pessoa`),
  CONSTRAINT `fk_ati_pre` FOREIGN KEY (`id_atividade_prerequisito`) REFERENCES `atividade` (`id_atividade`)
);

-- 6. Tabela Intermediária (N:M)
CREATE TABLE `inscricoes_atividade` (
  `id_participante` INT NOT NULL,
  `id_atividade` INT NOT NULL,
  `data_inscricao` DATETIME,
  `status_checkin` BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (`id_participante`, `id_atividade`),
  CONSTRAINT `fk_ins_par` FOREIGN KEY (`id_participante`) REFERENCES `participante` (`id_pessoa`),
  CONSTRAINT `fk_ins_ati` FOREIGN KEY (`id_atividade`) REFERENCES `atividade` (`id_atividade`)
);