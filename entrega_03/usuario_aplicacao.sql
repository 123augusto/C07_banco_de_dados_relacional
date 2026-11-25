-- Execute após festival_final.sql, com uma conta administradora.
-- Guarde a senha gerada pelo MySQL para iniciar a aplicação.
CREATE USER 'festival_app'@'127.0.0.1' IDENTIFIED BY RANDOM PASSWORD;
GRANT SELECT, INSERT, UPDATE, DELETE ON festival_inovacao_final.*
  TO 'festival_app'@'127.0.0.1';
