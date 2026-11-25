"""Executa o menu e confere os resultados no MySQL isolado do GitHub Actions."""

import os
from pathlib import Path
import subprocess
import sys

import pymysql


ENTREGA = Path(__file__).resolve().parents[1]


def carregar(nome):
    resultado = subprocess.run(
        ["docker", "exec", "-i", "c07-mysql", "mysql", "-uroot",
         "-pteste-isolado", "--default-character-set=utf8mb4", "-BNr"],
        input=(ENTREGA / nome).read_text(encoding="utf-8"),
        text=True, capture_output=True, timeout=30,
    )
    if resultado.returncode:
        raise RuntimeError(f"Falha ao executar {nome}. {resultado.stderr}")
    return resultado.stdout


def executar_menu(ambiente, *entradas):
    resultado = subprocess.run(
        [sys.executable, str(ENTREGA / "main.py")],
        input="\n".join([*entradas, "0", ""]),
        env=ambiente, text=True, capture_output=True, timeout=15,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "não concluíd" not in resultado.stdout, resultado.stdout
    return resultado.stdout


def main():
    carregar("festival_final.sql")
    senha = carregar("usuario_aplicacao.sql").splitlines()[0].split("\t")[2]
    ambiente = dict(os.environ, C07_DB_PASSWORD=senha)

    for tabela, quantidade in enumerate((11, 5, 6, 5, 6, 16, 5), 1):
        saida = executar_menu(ambiente, str(tabela), "2", "3", "1", "9999", "0")
        assert f"{quantidade} registro(s)." in saida and "Nenhum registro encontrado." in saida, saida
    saida = executar_menu(ambiente, "8", "1", "2", "3", "0")
    assert all(f"{n} registro(s)." in saida for n in (6, 5, 16)), saida
    assert "Luiza Freitas" in saida and "Sala de apoio" in saida, saida

    saida = executar_menu(ambiente, "1", "1", "Rita D'Ávila", "rita@example.com", "",
                          "3", "2", "Rita D'Ávila", "0")
    assert "ID: 12" in saida and "1 registro(s)." in saida, saida
    assert "Cadastro realizado" in executar_menu(ambiente, "3", "1", "12", "Estudante", "0")
    assert "Cadastro realizado" in executar_menu(ambiente, "6", "1", "12", "1", "", "",
                                                  "1", "12", "2", "", "", "0")
    assert "2 registro(s) alterado(s)" in executar_menu(ambiente, "6", "4", "2", "1", "1", "1", "12", "0")
    assert "Registro excluído" in executar_menu(ambiente, "6", "5", "12", "1", "SIM", "0")
    assert "Atualização cancelada" in executar_menu(ambiente, "4", "4", "2", "50", "2", "CANCELAR", "0")
    assert "5 registro(s) alterado(s)" in executar_menu(ambiente, "4", "4", "2", "50", "2", "TODOS", "0")

    with pymysql.connect(host="127.0.0.1", user="festival_app", password=senha,
                         database="festival_inovacao_final", charset="utf8mb4") as conexao:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT id_atividade, status_checkin, data_inscricao IS NOT NULL "
                           "FROM inscricoes_atividade WHERE id_participante=12")
            assert cursor.fetchall() == ((2, 1, 1),)
            cursor.execute("SELECT DISTINCT capacidade_maxima FROM espaco")
            assert cursor.fetchall() == ((50,),)
    print("MySQL 8: script final, conta da aplicação, trigger, JOINs e fluxos do menu conferidos.")


if __name__ == "__main__":
    main()
