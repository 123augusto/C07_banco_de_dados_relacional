"""Teste local do menu com SQLite em memória e o DDL de tabelas adaptado."""

from contextlib import redirect_stdout
from datetime import datetime
import io
from pathlib import Path
import re
import sqlite3
import sys
from unittest.mock import patch


raiz = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(raiz))
from banco import JOINS, TABELAS, buscar, consultar, excluir
from main import menu_principal


class Cursor(sqlite3.Cursor):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def execute(self, sql, params=()):
        return super().execute(sql.replace("%s", "?"), params)


class Conexao(sqlite3.Connection):
    def cursor(self):
        return super().cursor(factory=Cursor)


sqlite3.register_adapter(datetime, lambda data: data.isoformat(sep=" "))
db = sqlite3.connect(":memory:", factory=Conexao, isolation_level=None)
db.execute("PRAGMA foreign_keys = ON")
sql = (raiz / "festival_final.sql").read_text(encoding="utf-8")
ddl = re.findall(r"CREATE TABLE .*?\) ENGINE = InnoDB;", sql, re.S)
for tabela in ddl:
    db.execute(tabela.replace(" ENGINE = InnoDB", "").replace("INT AUTO_INCREMENT", "INTEGER"))
db.executescript(sql.split("START TRANSACTION;", 1)[1].split("COMMIT;", 1)[0])


def menu(*entradas):
    with patch("builtins.input", side_effect=[*entradas, "0"]), redirect_stdout(io.StringIO()) as saida:
        menu_principal(db, sqlite3.Error)
    return saida.getvalue()


def linhas(sql, params=()):
    return db.execute(sql, params).fetchall()


def inserir_menu(tabela, *valores):
    return menu(tabela, "1", *valores, "0")


def atualizar_menu(tabela, campo, valor, campo_filtro, valor_filtro):
    return menu(tabela, "4", campo, valor, "1", campo_filtro, valor_filtro, "0")


def excluir_menu(tabela, *chave):
    return menu(tabela, "5", *chave, "SIM", "0")


# As colunas do menu coincidem com o SQL final e cada tabela oferece as duas buscas.
for numero, tabela in enumerate(TABELAS, 1):
    campos = db.execute(f"PRAGMA table_info({tabela.nome})").fetchall()
    assert [campo.nome for campo in tabela.campos] == [campo[1] for campo in campos], tabela.nome
    assert [campo[1] for campo in campos if campo[5]] == list(tabela.chave), tabela.nome
    colunas, registros = buscar(db, tabela)
    assert len(registros) >= 5
    listagem = menu(str(numero), "2", "0")
    assert f"{len(registros)} registro(s)." in listagem, tabela.nome
    encontrado = menu(str(numero), "3", "1", str(registros[0][0]), "0")
    assert colunas[0] in encontrado and "Nenhum registro" not in encontrado, tabela.nome
    ausente = menu(str(numero), "3", "1", "99999", "0")
    assert "Nenhum registro encontrado" in ausente

_, credenciais = consultar(db, JOINS[0][1])
assert len(credenciais) == 6 and any(nome == "Luiza Freitas" and codigo is None for _, nome, _, codigo in credenciais)
_, espacos = consultar(db, JOINS[1][1])
assert len(espacos) == 5 and (5, "Sala de apoio", 30, 0) in espacos
_, inscritos = consultar(db, JOINS[2][1])
assert len(inscritos) == 16 and len({(linha[0], linha[2]) for linha in inscritos}) == 16
saida = menu("8", "1", "2", "3", "0")
assert all(resultados in saida for resultados in ("6 registro(s).", "5 registro(s).", "16 registro(s)."))

assert "ID: 12" in inserir_menu("1", "Rita D'Ávila", "rita@example.com", "")
assert "Rita D'Ávila" in menu("1", "3", "2", "Rita D'Ávila", "0")
assert "Rita D'Ávila" in menu("1", "3", "4", ":nulo", "0")
assert "1 registro(s) alterado(s)" in atualizar_menu("1", "3", "123", "2", "Rita D'Ávila")
assert "Cadastro realizado" in inserir_menu("2", "12", "Teste", "Robótica")
assert "1 registro(s) alterado(s)" in atualizar_menu("2", "2", "Educação", "1", "12")
assert "Cadastro realizado" in inserir_menu("3", "12", "Estudante")
assert "1 registro(s) alterado(s)" in atualizar_menu("3", "1", "Profissional", "1", "12")
assert "ID: 6" in inserir_menu("4", "Sala de Teste", "30")
assert "1 registro(s) alterado(s)" in atualizar_menu("4", "2", "45", "1", "6")
assert "ID: 7" in inserir_menu("5", "Teste", "", "90", "2026-12-01 12:25", "6", "12", "1")
assert "1 registro(s) alterado(s)" in atualizar_menu("5", "1", "Encontro", "1", "7")
assert "Cadastro realizado" in inserir_menu("6", "12", "7", "2026-12-01 12:05:00", "")
assert "Cadastro realizado" in inserir_menu("6", "12", "1", "2026-12-01 12:05:00", "")
assert "2 registro(s) alterado(s)" in atualizar_menu("6", "2", "1", "1", "12")
assert linhas("SELECT status_checkin FROM inscricoes_atividade WHERE id_participante=12") == [(1,), (1,)]
assert "ID: 6" in inserir_menu("7", "TESTE-12", "12")
assert "1 registro(s) alterado(s)" in atualizar_menu("7", "1", "NOVO-12", "2", "TESTE-12")

assert inserir_menu("7", "OUTRA-12", "12").count("Operação não concluída") == 1
assert inserir_menu("3", "999", "Estudante").count("Operação não concluída") == 1
assert inserir_menu("6", "12", "7", "", "").count("Operação não concluída") == 1

assert "Atualização cancelada" in menu("4", "4", "2", "50", "2", "NÃO", "0")
assert linhas("SELECT capacidade_maxima FROM espaco WHERE id_espaco=6") == [(45,)]
assert "6 registro(s) alterado(s)" in menu("4", "4", "2", "50", "2", "TODOS", "0")
assert linhas("SELECT DISTINCT capacidade_maxima FROM espaco") == [(50,)]

inscricoes = TABELAS[5]
for chave in ((), (12,), (None, 7)):
    try:
        excluir(db, inscricoes, chave)
    except ValueError:
        pass
    else:
        raise AssertionError("DELETE aceitou chave incompleta.")
assert "Exclusão cancelada" in menu("6", "5", "12", "7", "NÃO", "0")
assert len(linhas("SELECT id_atividade FROM inscricoes_atividade WHERE id_participante=12")) == 2
assert "Registro excluído" in excluir_menu("6", "12", "7")
assert linhas("SELECT id_atividade FROM inscricoes_atividade WHERE id_participante=12") == [(1,)]
assert "Registro não encontrado" in excluir_menu("6", "12", "7")
assert "Registro excluído" in excluir_menu("7", "6")
assert "Registro excluído" in excluir_menu("4", "6")
assert linhas("SELECT id_espaco FROM atividade WHERE id_atividade=7") == [(None,)]
assert "Registro excluído" in excluir_menu("2", "12")
assert linhas("SELECT id_palestrante FROM atividade WHERE id_atividade=7") == [(None,)]
assert "Registro excluído" in excluir_menu("3", "12")
assert linhas("SELECT id_atividade FROM inscricoes_atividade WHERE id_participante=12") == []
assert linhas("SELECT nome FROM pessoa WHERE id_pessoa=12") == [("Rita D'Ávila",)]
assert "Registro excluído" in excluir_menu("5", "7")
assert "Registro excluído" in excluir_menu("1", "12")

print("OK: 7 CRUDs, filtros vazio/exato/NULL, 3 joins, integridade e chave composta.")
