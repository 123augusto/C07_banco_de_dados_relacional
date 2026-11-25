"""Menu de terminal do Festival de Inovação do Inatel."""

from datetime import datetime
from getpass import getpass
import os

from banco import JOINS, TABELAS, atualizar, buscar, consultar, excluir, inserir


def escolher(titulo, opcoes, sair="Voltar"):
    print(f"\n{titulo}")
    for numero, opcao in enumerate(opcoes, 1):
        print(f"{numero}. {opcao}")
    print(f"0. {sair}")
    while True:
        entrada = input("Opção: ").strip()
        if entrada == "0":
            return None
        if entrada in {str(numero) for numero in range(1, len(opcoes) + 1)}:
            return int(entrada) - 1
        print("Escolha um número do menu.")


def ler_valor(campo, cadastro=False):
    instrucoes = {
        "texto": f"texto, até {campo.limite} caracteres",
        "inteiro": "número inteiro",
        "data e hora": "AAAA-MM-DD HH:MM[:SS]",
        "sim ou não": "1 para sim, 0 para não",
    }
    detalhes = [instrucoes[campo.tipo]]
    if campo.referencia:
        detalhes.append(f"ID em {campo.referencia}")
    if campo.opcional:
        detalhes.append(":nulo para NULL")
        if cadastro:
            detalhes.append(f"Enter para {campo.padrao if campo.padrao is not None else 'NULL'}")

    while True:
        entrada = input(f"{campo.nome} ({', '.join(detalhes)}): ").strip()
        if campo.opcional and entrada.casefold() == ":nulo":
            return None
        if not entrada:
            if cadastro and campo.opcional:
                return campo.padrao
            print("Informe um valor.")
            continue
        try:
            if campo.tipo == "inteiro":
                numero = int(entrada)
                if -(2**31) <= numero < 2**31:
                    return numero
            elif campo.tipo == "data e hora":
                formato = "%Y-%m-%d %H:%M:%S" if entrada.count(":") == 2 else "%Y-%m-%d %H:%M"
                data = datetime.strptime(entrada, formato)
                if data.year >= 1000:
                    return data
            elif campo.tipo == "sim ou não":
                if entrada in ("0", "1"):
                    return int(entrada)
            elif len(entrada) <= campo.limite:
                return entrada
        except ValueError:
            pass
        print(f"Valor inválido. Use {instrucoes[campo.tipo]}.")


def escolher_campo(titulo, campos, sair="Voltar"):
    opcao = escolher(titulo, [campo.nome for campo in campos], sair)
    return None if opcao is None else campos[opcao]


def exibir_resultado(colunas, registros):
    if not registros:
        print("Nenhum registro encontrado.")
        return
    linhas = [colunas] + [["NULL" if valor is None else str(valor) for valor in linha] for linha in registros]
    larguras = [max(len(valor) for valor in coluna) for coluna in zip(*linhas)]
    for numero, linha in enumerate(linhas):
        print(" | ".join(valor.ljust(largura) for valor, largura in zip(linha, larguras)))
        if numero == 0:
            print("-+-".join("-" * largura for largura in larguras))
    print(f"{len(registros)} registro(s).")


def cadastrar(conexao, tabela):
    valores = {}
    for campo in tabela.campos:
        if tabela.id_automatico and campo.nome in tabela.chave:
            continue
        valores[campo.nome] = ler_valor(campo, cadastro=True)
    novo_id = inserir(conexao, tabela, valores)
    if novo_id is None:
        print("Cadastro realizado.")
    else:
        print(f"Cadastro realizado. ID: {novo_id}.")


def editar(conexao, tabela):
    editaveis = [campo for campo in tabela.campos if campo.nome not in tabela.chave]
    campo = escolher_campo("Qual atributo deseja atualizar?", editaveis)
    if campo is None:
        return
    valor = ler_valor(campo)
    modo = escolher("Quais registros deseja atualizar?", ["Aplicar filtro", "Todos os registros"])
    if modo is None:
        return

    filtro = None
    if modo == 0:
        campo_filtro = escolher_campo("Qual atributo deseja usar como filtro?", tabela.campos)
        if campo_filtro is None:
            return
        filtro = campo_filtro, ler_valor(campo_filtro)
    elif input(f"A alteração afeta toda a tabela {tabela.nome}. Digite TODOS para confirmar: ").strip() != "TODOS":
        print("Atualização cancelada.")
        return

    print(f"{atualizar(conexao, tabela, campo, valor, filtro)} registro(s) alterado(s).")


def remover(conexao, tabela):
    print("Informe a chave primária do registro.")
    campos_chave = [campo for campo in tabela.campos if campo.nome in tabela.chave]
    chave = tuple(ler_valor(campo) for campo in campos_chave)
    identificacao = ", ".join(f"{campo.nome}={valor}" for campo, valor in zip(campos_chave, chave))
    if tabela.nome in {"pessoa", "participante", "palestrante", "atividade", "espaco"}:
        print("As regras do banco podem excluir ou desvincular registros relacionados.")
    if input(f"Excluir de {tabela.nome} ({identificacao})? Digite SIM para confirmar: ").strip() != "SIM":
        print("Exclusão cancelada.")
        return
    if excluir(conexao, tabela, chave):
        print("Registro excluído.")
    else:
        print("Registro não encontrado.")


def menu_tabela(conexao, tabela, erro_mysql):
    opcoes = ["Cadastrar", "Listar todos", "Buscar por filtro", "Atualizar", "Excluir pela chave primária"]
    while True:
        opcao = escolher(tabela.titulo, opcoes)
        try:
            if opcao is None:
                return
            if opcao == 0:
                cadastrar(conexao, tabela)
            elif opcao == 1:
                exibir_resultado(*buscar(conexao, tabela))
            elif opcao == 2:
                campo = escolher_campo("Filtrar por igualdade", tabela.campos)
                if campo is not None:
                    exibir_resultado(*buscar(conexao, tabela, (campo, ler_valor(campo))))
            elif opcao == 3:
                editar(conexao, tabela)
            elif opcao == 4:
                remover(conexao, tabela)
        except erro_mysql as erro:
            print(f"Operação não concluída pelo MySQL. {erro}")


def menu_joins(conexao, erro_mysql):
    while True:
        opcao = escolher("Consultas com JOIN", [titulo for titulo, _ in JOINS])
        if opcao is None:
            return
        titulo, sql = JOINS[opcao]
        print(f"\n{titulo}")
        try:
            exibir_resultado(*consultar(conexao, sql))
        except erro_mysql as erro:
            print(f"Consulta não concluída pelo MySQL. {erro}")


def menu_principal(conexao, erro_mysql):
    opcoes = [tabela.titulo for tabela in TABELAS] + ["Consultas com JOIN"]
    while True:
        opcao = escolher("Festival de Inovação do Inatel", opcoes, "Sair")
        if opcao is None:
            return
        if opcao == len(TABELAS):
            menu_joins(conexao, erro_mysql)
        else:
            menu_tabela(conexao, TABELAS[opcao], erro_mysql)


def main():
    try:
        import pymysql
    except ModuleNotFoundError:
        print("Instale a dependência com python -m pip install -r entrega_03/requirements.txt.")
        return 1

    usuario = os.getenv("C07_DB_USER", "festival_app")
    try:
        porta = int(os.getenv("C07_DB_PORT", "3306"))
        if not 1 <= porta <= 65535:
            raise ValueError
    except ValueError:
        print("C07_DB_PORT deve ser um número inteiro entre 1 e 65535.")
        return 1

    try:
        senha = os.getenv("C07_DB_PASSWORD")
        if senha is None:
            senha = getpass(f"Senha MySQL de {usuario}: ")
        with pymysql.connect(
            host=os.getenv("C07_DB_HOST", "127.0.0.1"),
            port=porta,
            user=usuario,
            password=senha,
            database=os.getenv("C07_DB_NAME", "festival_inovacao_final"),
            charset="utf8mb4",
            autocommit=True,
            connect_timeout=5,
        ) as conexao:
            menu_principal(conexao, pymysql.MySQLError)
    except pymysql.MySQLError as erro:
        print(f"Falha na conexão com o MySQL. {erro}")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nSessão encerrada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
