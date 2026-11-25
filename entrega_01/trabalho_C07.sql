-- Festival de Inovacao: modelo revisado para a disciplina C07.
-- Executar em um banco festival_inovacao sem as tabelas deste projeto.
-- Este arquivo cria a estrutura; nao migra tabelas que ja existam.
-- A data de inscricao deve ser informada quando conhecida; nao e automatica.

CREATE DATABASE IF NOT EXISTS festival_inovacao;
USE festival_inovacao;

CREATE TABLE pessoa (
  id_pessoa INT AUTO_INCREMENT,
  nome VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL UNIQUE,
  telefone VARCHAR(15),
  PRIMARY KEY (id_pessoa)
);

CREATE TABLE palestrante (
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

CREATE TABLE participante (
  id_pessoa INT,
  tipo_ingresso VARCHAR(20) NOT NULL,
  PRIMARY KEY (id_pessoa),
  CONSTRAINT fk_participante_pessoa
    FOREIGN KEY (id_pessoa)
    REFERENCES pessoa (id_pessoa)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

CREATE TABLE espaco (
  id_espaco INT AUTO_INCREMENT,
  nome_local VARCHAR(50) NOT NULL,
  capacidade_maxima INT NOT NULL,
  PRIMARY KEY (id_espaco)
);

CREATE TABLE atividade (
  id_atividade INT AUTO_INCREMENT,
  titulo VARCHAR(150) NOT NULL,
  descricao VARCHAR(255),
  duracao_minutos INT,
  data_hora_inicio DATETIME NOT NULL, 
  id_espaco INT,
  id_palestrante INT,
  id_atividade_prerequisito INT, 
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

CREATE TABLE inscricoes_atividade (
  id_participante INT,
  id_atividade INT,
  data_inscricao DATETIME,
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

-- Relacionamento 1:1: um participante pode possuir no maximo uma credencial.
-- NOT NULL exige o participante; UNIQUE impede duas credenciais para ele.
CREATE TABLE credencial (
  id_credencial INT AUTO_INCREMENT,
  codigo VARCHAR(30) NOT NULL UNIQUE,
  id_participante INT NOT NULL UNIQUE,
  PRIMARY KEY (id_credencial),
  CONSTRAINT fk_credencial_participante
    FOREIGN KEY (id_participante)
    REFERENCES participante (id_pessoa)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);
