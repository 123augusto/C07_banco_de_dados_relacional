-- -----------------------------------------------------
-- Criação do Banco de Dados
-- -----------------------------------------------------
CREATE DATABASE IF NOT EXISTS festival_inovacao;
USE festival_inovacao;

-- -----------------------------------------------------
-- Tabela 1: pessoa (Superclasse - Layer: Gestão de Pessoas)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS pessoa (
  id_pessoa INT AUTO_INCREMENT,
  nome VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL UNIQUE,
  telefone VARCHAR(15),
  PRIMARY KEY (id_pessoa)
);

-- -----------------------------------------------------
-- Tabela 2: palestrante (Subclasse)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS palestrante (
  id_pessoa INT,
  minicurriculo VARCHAR(255),
  area_especialidade VARCHAR(50),
  PRIMARY KEY (id_pessoa),
  CONSTRAINT fk_palestrante_pessoa
    FOREIGN KEY (id_pessoa)
    REFERENCES pessoa (id_pessoa)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

-- -----------------------------------------------------
-- Tabela 3: participante (Subclasse)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS participante (
  id_pessoa INT,
  tipo_ingresso VARCHAR(20) NOT NULL,
  PRIMARY KEY (id_pessoa),
  CONSTRAINT fk_participante_pessoa
    FOREIGN KEY (id_pessoa)
    REFERENCES pessoa (id_pessoa)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

-- -----------------------------------------------------
-- Tabela 4: espaco (Layer: Gestão do Evento)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS espaco (
  id_espaco INT AUTO_INCREMENT,
  nome_local VARCHAR(50) NOT NULL,
  capacidade_maxima INT NOT NULL,
  PRIMARY KEY (id_espaco)
);

-- -----------------------------------------------------
-- Tabela 5: atividade (Contém o Relacionamento Recursivo)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS atividade (
  id_atividade INT AUTO_INCREMENT,
  titulo VARCHAR(150) NOT NULL,
  descricao VARCHAR(255),
  duracao_minutos INT,
  data_hora_inicio DATETIME NOT NULL, -- ATRIBUTO NOVO INCLUÍDO AQUI
  id_espaco INT,
  id_palestrante INT,
  id_atividade_prerequisito INT, -- RECURSIVIDADE
  PRIMARY KEY (id_atividade),
  
  CONSTRAINT fk_atividade_espaco
    FOREIGN KEY (id_espaco)
    REFERENCES espaco (id_espaco)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
    
  CONSTRAINT fk_atividade_palestrante
    FOREIGN KEY (id_palestrante)
    REFERENCES palestrante (id_pessoa)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
    
  CONSTRAINT fk_atividade_recursiva
    FOREIGN KEY (id_atividade_prerequisito)
    REFERENCES atividade (id_atividade)
    ON DELETE SET NULL
    ON UPDATE CASCADE
);

-- -----------------------------------------------------
-- Tabela 6: inscricoes_atividade (Relacionamento N:M)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS inscricoes_atividade (
  id_participante INT,
  id_atividade INT,
  data_inscricao DATETIME DEFAULT CURRENT_TIMESTAMP,
  status_checkin BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (id_participante, id_atividade),
  
  CONSTRAINT fk_inscricao_participante
    FOREIGN KEY (id_participante)
    REFERENCES participante (id_pessoa)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
    
  CONSTRAINT fk_inscricao_atividade
    FOREIGN KEY (id_atividade)
    REFERENCES atividade (id_atividade)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);