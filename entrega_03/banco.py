"""Tabelas e comandos SQL usados pelo menu do festival."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Campo:
    nome: str
    tipo: str = "texto"
    opcional: bool = False
    limite: int = 0
    referencia: str = ""
    padrao: int | None = None


@dataclass(frozen=True)
class Tabela:
    nome: str
    titulo: str
    chave: tuple[str, ...]
    campos: tuple[Campo, ...]
    id_automatico: bool = False


TABELAS = (
    Tabela("pessoa", "Pessoas", ("id_pessoa",), (
        Campo("id_pessoa", "inteiro"),
        Campo("nome", limite=100),
        Campo("email", limite=100),
        Campo("telefone", opcional=True, limite=15),
    ), id_automatico=True),
    Tabela("palestrante", "Palestrantes", ("id_pessoa",), (
        Campo("id_pessoa", "inteiro", referencia="pessoa"),
        Campo("minicurriculo", opcional=True, limite=255),
        Campo("area_especialidade", opcional=True, limite=50),
    )),
    Tabela("participante", "Participantes", ("id_pessoa",), (
        Campo("id_pessoa", "inteiro", referencia="pessoa"),
        Campo("tipo_ingresso", limite=20),
    )),
    Tabela("espaco", "Espaços", ("id_espaco",), (
        Campo("id_espaco", "inteiro"),
        Campo("nome_local", limite=50),
        Campo("capacidade_maxima", "inteiro"),
    ), id_automatico=True),
    Tabela("atividade", "Atividades", ("id_atividade",), (
        Campo("id_atividade", "inteiro"),
        Campo("titulo", limite=150),
        Campo("descricao", opcional=True, limite=255),
        Campo("duracao_minutos", "inteiro", opcional=True),
        Campo("data_hora_inicio", "data e hora"),
        Campo("id_espaco", "inteiro", opcional=True, referencia="espaco"),
        Campo("id_palestrante", "inteiro", opcional=True, referencia="palestrante"),
        Campo("id_atividade_prerequisito", "inteiro", opcional=True, referencia="atividade"),
    ), id_automatico=True),
    Tabela("inscricoes_atividade", "Inscrições", ("id_participante", "id_atividade"), (
        Campo("id_participante", "inteiro", referencia="participante"),
        Campo("id_atividade", "inteiro", referencia="atividade"),
        Campo("data_inscricao", "data e hora", opcional=True),
        Campo("status_checkin", "sim ou não", opcional=True, padrao=0),
    )),
    Tabela("credencial", "Credenciais", ("id_credencial",), (
        Campo("id_credencial", "inteiro"),
        Campo("codigo", limite=30),
        Campo("id_participante", "inteiro", referencia="participante"),
    ), id_automatico=True),
)


JOINS = (
    ("1:1 | Participantes e credenciais", """
        SELECT pessoa.id_pessoa, pessoa.nome, participante.tipo_ingresso,
               credencial.codigo AS credencial
        FROM participante
        JOIN pessoa ON pessoa.id_pessoa = participante.id_pessoa
        LEFT JOIN credencial ON credencial.id_participante = participante.id_pessoa
        ORDER BY pessoa.nome, pessoa.id_pessoa
    """),
    ("1:N | Atividades por espaço", """
        SELECT espaco.id_espaco, espaco.nome_local, espaco.capacidade_maxima,
               COUNT(atividade.id_atividade) AS total_atividades
        FROM espaco
        LEFT JOIN atividade ON atividade.id_espaco = espaco.id_espaco
        GROUP BY espaco.id_espaco, espaco.nome_local, espaco.capacidade_maxima
        ORDER BY total_atividades DESC, espaco.nome_local, espaco.id_espaco
    """),
    ("N:M | Inscrições de participantes em atividades", """
        SELECT inscricao.id_participante, pessoa.nome AS participante,
               inscricao.id_atividade, atividade.titulo AS atividade,
               inscricao.data_inscricao, inscricao.status_checkin
        FROM inscricoes_atividade AS inscricao
        JOIN participante ON participante.id_pessoa = inscricao.id_participante
        JOIN pessoa ON pessoa.id_pessoa = participante.id_pessoa
        JOIN atividade ON atividade.id_atividade = inscricao.id_atividade
        ORDER BY pessoa.nome, inscricao.id_participante, inscricao.id_atividade
    """),
)


def condicao(filtro):
    if filtro is None:
        return "", ()
    campo, valor = filtro
    if valor is None:
        return f" WHERE {campo.nome} IS NULL", ()
    return f" WHERE {campo.nome} = %s", (valor,)


def consultar(conexao, sql, parametros=()):
    with conexao.cursor() as cursor:
        cursor.execute(sql, parametros)
        colunas = [coluna[0] for coluna in cursor.description]
        return colunas, cursor.fetchall()


def buscar(conexao, tabela, filtro=None):
    # Nomes de tabelas e colunas vêm das opções definidas em TABELAS.
    where, parametros = condicao(filtro)
    colunas = ", ".join(campo.nome for campo in tabela.campos)
    ordem = ", ".join(tabela.chave)
    return consultar(conexao, f"SELECT {colunas} FROM {tabela.nome}{where} ORDER BY {ordem}", parametros)


def inserir(conexao, tabela, valores):
    colunas = ", ".join(valores)
    marcadores = ", ".join("%s" for _ in valores)
    sql = f"INSERT INTO {tabela.nome} ({colunas}) VALUES ({marcadores})"
    with conexao.cursor() as cursor:
        cursor.execute(sql, tuple(valores.values()))
        return cursor.lastrowid if tabela.id_automatico else None


def atualizar(conexao, tabela, campo, valor, filtro):
    where, parametros = condicao(filtro)
    sql = f"UPDATE {tabela.nome} SET {campo.nome} = %s{where}"
    with conexao.cursor() as cursor:
        cursor.execute(sql, (valor, *parametros))
        return cursor.rowcount


def excluir(conexao, tabela, chave):
    if len(chave) != len(tabela.chave) or not chave or None in chave:
        raise ValueError("Informe todos os valores da chave primária para excluir.")
    where = " AND ".join(f"{coluna} = %s" for coluna in tabela.chave)
    with conexao.cursor() as cursor:
        cursor.execute(f"DELETE FROM {tabela.nome} WHERE {where}", chave)
        return cursor.rowcount
