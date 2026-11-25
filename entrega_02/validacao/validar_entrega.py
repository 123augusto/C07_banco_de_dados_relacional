"""Valida a entrega em MySQL temporario, sem conectar a bancos existentes.

Usa somente Python padrao e os executaveis MySQL ja instalados.
O servidor temporario aceita conexoes apenas em 127.0.0.1, em porta livre.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import unescape


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "gerados"
BIN = Path(os.environ.get("C07_MYSQL_BIN", r"C:\Program Files\MySQL\MySQL Server 8.0\bin"))
DB = "festival_inovacao_segunda_entrega"
HIDDEN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def read_diagram(path: Path):
    root = ET.parse(path).getroot()
    pages = root.findall("diagram")
    tables = {}
    for cell in pages[1].findall(".//mxCell"):
        if not cell.get("id", "").endswith("_rows"):
            continue
        columns = []
        for line in cell.get("value", "").splitlines():
            match = re.fullmatch(r"(\w+)\s+([A-Z]+(?:\([0-9,]+\))?)(?:\s+\[([^]]+)\])?", line.strip())
            if match is None:
                raise AssertionError(f"Linha do diagrama nao reconhecida: {line!r}")
            name, column_type, flags_text = match.groups()
            flags_text = flags_text or ""
            flags = {part.strip() for part in flags_text.split(",")}
            reference = re.search(r"FK\s*→\s*(\w+)", flags_text)
            columns.append({
                "name": name, "type": column_type.lower(),
                "pk": "PK" in flags or "PK*" in flags,
                "unique": "U" in flags, "required": "NN" in flags,
                "auto": "AI" in flags,
                "default": "0" if "DEFAULT FALSE" in flags else "<NULL>",
                "reference": reference.group(1) if reference else None,
            })
        tables[cell.get("parent")] = columns
    signatures = []
    for page in pages:
        cells = []
        for cell in page.findall(".//mxCell"):
            # Notas explicativas ausentes no arquivo recebido, sem alterar o modelo.
            if cell.get("id") in {"legend1", "legend2", "intermediaria"}:
                continue
            value = unescape(cell.get("value", ""))
            value = re.sub(r"<br\s*/?>", " ", value)
            value = " ".join(re.sub(r"<[^>]*>", "", value).split())
            if value or cell.get("edge") == "1":
                cells.append((cell.get("id", ""), value, cell.get("source", ""), cell.get("target", "")))
        signatures.append((page.get("name"), sorted(cells)))
    return tables, signatures


def main() -> None:
    OUT.mkdir(exist_ok=True)
    server_exe = BIN / "mysqld.exe"
    client_exe = BIN / "mysql.exe"
    admin_exe = BIN / "mysqladmin.exe"
    for exe in (server_exe, client_exe, admin_exe):
        if not exe.is_file():
            raise RuntimeError(f"Executavel ausente: {exe}. Nada foi instalado.")

    diagram_hash = hashlib.sha256((ROOT / "segundaEntrega.drawio").read_bytes()).hexdigest()
    expected_tables, diagram_signature = read_diagram(ROOT / "segundaEntrega.drawio")
    run_date = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y")
    workspace = Path(tempfile.mkdtemp(prefix="c07_segunda_entrega_"))
    data = workspace / "data"
    data.mkdir()
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    checks: list[str] = []
    server = None
    log_file = None
    stopped = False

    def run_sql(sql: str, user: str = "root", password: str | None = None):
        env = os.environ.copy()
        env.pop("MYSQL_PWD", None)
        if password is not None:
            env["MYSQL_PWD"] = password
        return subprocess.run(
            [str(client_exe), "--no-defaults", "--protocol=TCP", "--host=127.0.0.1",
             f"--port={port}", f"--user={user}", "--default-character-set=utf8mb4",
             "--batch", "--raw", "--skip-column-names"],
            input=sql, text=True, encoding="utf-8", capture_output=True,
            timeout=25, creationflags=HIDDEN, env=env,
        )

    def good(label: str, sql: str, expected: str | None = None,
             user: str = "root", password: str | None = None) -> str:
        result = run_sql(sql, user, password)
        if result.returncode:
            raise AssertionError(f"{label}: {result.stderr}")
        actual = result.stdout.strip()
        if expected is not None and actual != expected:
            raise AssertionError(f"{label}: esperado {expected!r}, obtido {actual!r}")
        checks.append(label)
        print(f"OK {len(checks):02d}: {label}", flush=True)
        return actual

    def bad(label: str, sql: str, error: int,
            user: str = "root", password: str | None = None) -> None:
        result = run_sql(f"USE {DB};\n{sql}", user, password)
        if result.returncode == 0 or f"ERROR {error} " not in result.stderr:
            raise AssertionError(f"{label}: erro {error} esperado, obtido {result.stderr!r}")
        checks.append(label)
        print(f"OK {len(checks):02d}: {label}", flush=True)

    def local(sql: str) -> str:
        return f"USE {DB};\n{sql}"

    try:
        initialized = subprocess.run(
            [str(server_exe), "--no-defaults", "--initialize-insecure",
             f"--basedir={BIN.parent}", f"--datadir={data}",
             f"--log-error={workspace / 'initialization.log'}"],
            capture_output=True, text=True, timeout=90, creationflags=HIDDEN,
        )
        if initialized.returncode:
            raise RuntimeError(f"Inicializacao falhou: {initialized.stderr}; logs em {workspace}")

        log_file = (workspace / "process.log").open("wb")
        server = subprocess.Popen(
            [str(server_exe), "--no-defaults", f"--basedir={BIN.parent}",
             f"--datadir={data}", "--bind-address=127.0.0.1", f"--port={port}",
             "--mysqlx=0", "--skip-log-bin", "--skip-name-resolve=OFF", "--innodb-buffer-pool-size=32M",
             "--performance-schema=OFF", f"--log-error={workspace / 'server.log'}"],
            stdout=log_file, stderr=subprocess.STDOUT, creationflags=HIDDEN,
        )
        deadline = time.monotonic() + 50
        while time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError(f"Servidor encerrou antes dos testes. Logs em {workspace}")
            probe = run_sql("SELECT @@datadir;")
            if probe.returncode == 0:
                actual_data = Path(probe.stdout.strip()).resolve()
                if actual_data != data.resolve():
                    raise RuntimeError("A conexao nao corresponde ao diretorio temporario. Abortado.")
                break
            time.sleep(0.25)
        else:
            raise RuntimeError("Tempo esgotado ao iniciar servidor temporario.")

        version = good("Servidor temporario identificado", "SELECT VERSION();")
        main_sql = (ROOT / "segundaEntrega.sql").read_text(encoding="utf-8")
        sql_output = good("Script principal executado integralmente", main_sql)
        (OUT / "saida_script_principal.txt").write_text(sql_output + "\n", encoding="utf-8")
        roles_sql = (ROOT / "usuarios_roles.sql").read_text(encoding="utf-8")
        roles_saida = good("Script de dois usuarios e ROLE executado", roles_sql)
        senhas_geradas = {}
        for linha in roles_saida.splitlines():
            colunas = linha.split("\t")
            if len(colunas) >= 3 and colunas[0] in {"recepcao_ana", "recepcao_bruno"}:
                senhas_geradas[colunas[0]] = colunas[2]
        if len(senhas_geradas) != 2:
            raise RuntimeError("O MySQL nao retornou as duas senhas geradas.")

        counts = good("Minimo de cinco registros em cada uma das sete tabelas", local("""
SELECT 'atividade', COUNT(*) FROM atividade
UNION ALL SELECT 'credencial', COUNT(*) FROM credencial
UNION ALL SELECT 'espaco', COUNT(*) FROM espaco
UNION ALL SELECT 'inscricoes_atividade', COUNT(*) FROM inscricoes_atividade
UNION ALL SELECT 'palestrante', COUNT(*) FROM palestrante
UNION ALL SELECT 'participante', COUNT(*) FROM participante
UNION ALL SELECT 'pessoa', COUNT(*) FROM pessoa;
"""), "atividade\t6\ncredencial\t5\nespaco\t5\ninscricoes_atividade\t16\npalestrante\t5\nparticipante\t6\npessoa\t11")

        # A fonte esperada e o Draw.io, nao as declaracoes do script SQL.
        original = ROOT.parent / "entrega_01" / "Festival_corrigido.drawio"
        _, original_signature = read_diagram(original)
        if diagram_signature != original_signature:
            raise AssertionError("Os modelos Draw.io diferem em rotulos, atributos ou vinculos.")
        checks.append("Diagrama recebido preserva entidades, atributos, cardinalidades e vinculos anteriores")

        good("Exatamente as sete tabelas previstas no diagrama", f"SELECT table_name FROM information_schema.tables WHERE table_schema='{DB}' AND table_type='BASE TABLE' ORDER BY table_name;", "\n".join(sorted(expected_tables)))
        expected_uniques = []
        expected_foreign_keys = []
        for table, columns in expected_tables.items():
            expected_column_rows = []
            for col in columns:
                sql_type = "tinyint(1)" if col["type"] == "boolean" else col["type"]
                nullable = "NO" if col["pk"] or col["required"] else "YES"
                extra = "auto_increment" if col["auto"] else ""
                expected_column_rows.append("\t".join([col["name"], sql_type, nullable, col["default"], extra]))
                if col["unique"]:
                    expected_uniques.append((table, col["name"]))
                if col["reference"]:
                    parent_keys = [c["name"] for c in expected_tables[col["reference"]] if c["pk"]]
                    if len(parent_keys) != 1:
                        raise AssertionError("Referencia do diagrama exige conferencia de chave composta.")
                    # Acoes referenciais tambem conferidas contra o SQL da primeira entrega.
                    delete_rule = "SET NULL" if table == "atividade" else "CASCADE"
                    expected_foreign_keys.append((table, col["name"], col["reference"], parent_keys[0], "CASCADE", delete_rule))
            expected_metadata = "\n".join(expected_column_rows).rstrip()
            good(f"{table}: colunas, tipos, nulabilidade, defaults e AUTO_INCREMENT conforme o Draw.io", f"""
SELECT column_name,column_type,is_nullable,COALESCE(column_default,'<NULL>'),extra
FROM information_schema.columns
WHERE table_schema='{DB}' AND table_name='{table}' ORDER BY ordinal_position;
""", expected_metadata)
            good(f"{table}: chave primaria conforme o Draw.io", f"SELECT column_name FROM information_schema.key_column_usage WHERE table_schema='{DB}' AND table_name='{table}' AND constraint_name='PRIMARY' ORDER BY ordinal_position;", "\n".join(c["name"] for c in columns if c["pk"]))

        good("Restricoes UNIQUE correspondem ao diagrama", f"SELECT table_name,column_name FROM information_schema.statistics WHERE table_schema='{DB}' AND non_unique=0 AND index_name<>'PRIMARY' ORDER BY table_name,column_name;", "\n".join("\t".join(row) for row in sorted(expected_uniques)))
        good("Todas as FKs preservam os vinculos e as acoes referenciais anteriores", f"""
SELECT k.table_name,k.column_name,k.referenced_table_name,k.referenced_column_name,r.update_rule,r.delete_rule
FROM information_schema.key_column_usage AS k
JOIN information_schema.referential_constraints AS r
  ON r.constraint_schema=k.constraint_schema AND r.table_name=k.table_name AND r.constraint_name=k.constraint_name
WHERE k.table_schema='{DB}' AND k.referenced_table_name IS NOT NULL
ORDER BY k.table_name,k.column_name;
""", "\n".join("\t".join(row) for row in sorted(expected_foreign_keys)))

        query_expectations = {
            1: "6\tFelipe Costa\tEstudante\tFEST-2026-006\n7\tGabriela Dias\tProfissional\tFEST-2026-007\n8\tHenrique Reis\tEstudante\tFEST-2026-008\n9\tIsabela Nunes\tEstudante\tFEST-2026-009\n10\tJoao Martins\tProfissional\tFEST-2026-010\n11\tLuiza Freitas\tEstudante\tNULL",
            2: "1\tAuditorio principal\t120\t2\t120\n2\tLaboratorio de robotica\t40\t1\t90\n3\tSala de desenvolvimento\t60\t1\t90\n4\tSala de empreendedorismo\t80\t1\t60\n5\tSala de apoio\t30\t0\tNULL",
            3: "10\tJoao Martins\t4\t270\t1\n6\tFelipe Costa\t3\t240\t1\n7\tGabriela Dias\t3\t210\t2\n8\tHenrique Reis\t3\t210\t1\n9\tIsabela Nunes\t3\t210\t1",
            4: "Felipe Costa\tFEST-2026-006\tIntroducao a sistemas inteligentes\tAuditorio principal\tAna Melo\t2026-10-20 08:00:00\nGabriela Dias\tFEST-2026-007\tIntroducao a sistemas inteligentes\tAuditorio principal\tAna Melo\t2026-10-21 09:00:00\nHenrique Reis\tFEST-2026-008\tIntroducao a sistemas inteligentes\tAuditorio principal\tAna Melo\t2026-10-22 10:00:00\nGabriela Dias\tFEST-2026-007\tSoftware acessivel\tSala de desenvolvimento\tCarla Souza\t2026-10-21 09:05:00\nIsabela Nunes\tFEST-2026-009\tSoftware acessivel\tSala de desenvolvimento\tCarla Souza\t2026-10-23 11:00:00\nJoao Martins\tFEST-2026-010\tRedes para projetos conectados\tAuditorio principal\tElisa Rocha\t2026-10-24 12:15:00",
            5: "Robotica na pratica\tIntroducao a sistemas inteligentes\nRedes para projetos conectados\tIntroducao a sistemas inteligentes",
            6: "11\tLuiza Freitas",
        }
        for number, expected in query_expectations.items():
            start = main_sql.index(f"-- Q{number} |")
            end_marker = f"-- Q{number+1} |" if number < 6 else "-- 8. "
            end = main_sql.index(end_marker, start)
            good(f"Q{number}: resultado integral da consulta JOIN conferido", local(main_sql[start:end]), expected)

        good("Pessoa pode existir sem pertencer a uma subclasse", local("START TRANSACTION; INSERT INTO pessoa(id_pessoa,nome,email) VALUES(99,'Teste de especializacao','especializacao@example.com'); SELECT (SELECT COUNT(*) FROM palestrante WHERE id_pessoa=99),(SELECT COUNT(*) FROM participante WHERE id_pessoa=99); ROLLBACK;"), "0\t0")
        good("Palestrante pode ministrar mais de uma atividade", local("START TRANSACTION; UPDATE atividade SET id_palestrante=1 WHERE id_atividade=6; SELECT COUNT(*) FROM atividade WHERE id_palestrante=1; ROLLBACK;"), "2")

        good("Trigger preenche data de inscricao ausente", local("""
START TRANSACTION;
SET @antes = NOW();
INSERT INTO inscricoes_atividade(id_participante,id_atividade,data_inscricao) VALUES(11,6,NULL);
SELECT data_inscricao IS NOT NULL AND data_inscricao >= @antes AND data_inscricao <= NOW()
FROM inscricoes_atividade WHERE id_participante=11 AND id_atividade=6;
ROLLBACK;
"""), "1")
        good("Trigger preserva data de inscricao informada", local("""
START TRANSACTION;
INSERT INTO inscricoes_atividade(id_participante,id_atividade,data_inscricao)
VALUES(11,6,'2026-10-20 09:00:00');
SELECT data_inscricao FROM inscricoes_atividade WHERE id_participante=11 AND id_atividade=6;
ROLLBACK;
"""), "2026-10-20 09:00:00")
        good("DML corrige telefone e cancela apenas a inscricao demonstrada", local("""
SELECT telefone FROM pessoa WHERE id_pessoa=6;
SELECT COUNT(*) FROM participante WHERE id_pessoa=11;
SELECT COUNT(*) FROM inscricoes_atividade WHERE id_participante=11;
"""), "11900000006\n1\n0")
        good("Heranca permite sobreposicao de subclasses", local("""
START TRANSACTION;
INSERT INTO participante VALUES (1,'Convidado');
SELECT COUNT(*) FROM palestrante AS p JOIN participante AS t ON t.id_pessoa=p.id_pessoa WHERE p.id_pessoa=1;
ROLLBACK;
"""), "1")
        bad("Heranca rejeita subclasse sem pessoa", "INSERT INTO palestrante VALUES(999,'Teste','Teste');", 1452)
        bad("N:M rejeita inscricao duplicada", "INSERT INTO inscricoes_atividade(id_participante,id_atividade) VALUES(6,1);", 1062)
        bad("1:1 rejeita segunda credencial do mesmo participante", "INSERT INTO credencial(codigo,id_participante) VALUES('OUTRA',6);", 1062)
        bad("Credencial exige participante nao nulo", "INSERT INTO credencial(codigo,id_participante) VALUES('SEM-PESSOA',NULL);", 1048)
        bad("Credencial rejeita participante inexistente", "INSERT INTO credencial(codigo,id_participante) VALUES('INEXISTENTE',999);", 1452)
        bad("UNIQUE rejeita email duplicado", "INSERT INTO pessoa(nome,email) VALUES('Teste','ana.melo@example.com');", 1062)
        bad("Autorrelacionamento rejeita pre-requisito inexistente", "UPDATE atividade SET id_atividade_prerequisito=999 WHERE id_atividade=6;", 1452)
        good("Procedure informa ausencia sem criar inscricao", local("CALL sp_registrar_checkin(11,1); SELECT COUNT(*) FROM inscricoes_atividade WHERE id_participante=11 AND id_atividade=1;"), "Inscricao nao encontrada.\n0")
        good("Procedure permite repetir check-in ja confirmado", local("CALL sp_registrar_checkin(8,1); CALL sp_registrar_checkin(8,1); SELECT status_checkin FROM inscricoes_atividade WHERE id_participante=8 AND id_atividade=1;"), "Check-in registrado.\nCheck-in registrado.\n1")
        good("Function calcula percentual e trata denominador zero", local("SELECT fn_percentual_presenca(3,4),fn_percentual_presenca(2,3),fn_percentual_presenca(0,0),fn_percentual_presenca(NULL,4),fn_percentual_presenca(1,NULL);"), "75.00\t66.67\t0.00\tNULL\tNULL")
        good("View e function mantem atividades vazias e calculam percentuais", local("SELECT id_atividade,total_inscritos,total_checkins,fn_percentual_presenca(total_checkins,total_inscritos) FROM vw_resumo_atividades ORDER BY id_atividade;"), "1\t4\t3\t75.00\n2\t3\t0\t0.00\n3\t3\t2\t66.67\n4\t3\t0\t0.00\n5\t3\t1\t33.33\n6\t0\t0\t0.00")
        good("Relatorio reflete novas inscricoes e check-ins", local("START TRANSACTION; INSERT INTO inscricoes_atividade(id_participante,id_atividade,status_checkin) VALUES(11,6,TRUE); SELECT total_inscritos,total_checkins,fn_percentual_presenca(total_checkins,total_inscritos) FROM vw_resumo_atividades WHERE id_atividade=6; ROLLBACK;"), "1\t1\t100.00")
        good("Check-in NULL nao e contado como presenca", local("START TRANSACTION; INSERT INTO inscricoes_atividade(id_participante,id_atividade,status_checkin) VALUES(11,6,NULL); SELECT total_inscritos,total_checkins,fn_percentual_presenca(total_checkins,total_inscritos) FROM vw_resumo_atividades WHERE id_atividade=6; ROLLBACK;"), "1\t0\t0.00")
        good("DELETE CASCADE remove dependencias da pessoa", local("START TRANSACTION; DELETE FROM pessoa WHERE id_pessoa=6; SELECT (SELECT COUNT(*) FROM participante WHERE id_pessoa=6),(SELECT COUNT(*) FROM credencial WHERE id_participante=6),(SELECT COUNT(*) FROM inscricoes_atividade WHERE id_participante=6); ROLLBACK;"), "0\t0\t0")
        good("DELETE SET NULL preserva atividade sem espaco", local("START TRANSACTION; DELETE FROM espaco WHERE id_espaco=2; SELECT id_espaco IS NULL FROM atividade WHERE id_atividade=2; ROLLBACK;"), "1")
        good("DELETE SET NULL preserva atividade sem palestrante", local("START TRANSACTION; DELETE FROM palestrante WHERE id_pessoa=2; SELECT id_palestrante IS NULL FROM atividade WHERE id_atividade=2; ROLLBACK;"), "1")
        good("Exclusao do pre-requisito preserva as atividades dependentes", local("START TRANSACTION; DELETE FROM atividade WHERE id_atividade=1; SELECT COUNT(*) FROM atividade WHERE id_atividade IN(2,5) AND id_atividade_prerequisito IS NULL; ROLLBACK;"), "2")

        for user, password in senhas_geradas.items():
            good(f"{user}: ROLE ativa por padrao", "SELECT CURRENT_ROLE();", "`r_recepcao_festival`@`%`", user, password)
            good(f"{user}: consulta view e function e executa procedure", local("SELECT COUNT(*) FROM vw_resumo_atividades; SELECT fn_percentual_presenca(3,4); CALL sp_registrar_checkin(8,1);"), "6\n75.00\nCheck-in registrado.", user, password)
            good(f"{user}: UPDATE permitido na coluna check-in", local("START TRANSACTION; UPDATE inscricoes_atividade SET status_checkin=TRUE WHERE id_participante=10 AND id_atividade=1; SELECT status_checkin FROM inscricoes_atividade WHERE id_participante=10 AND id_atividade=1; ROLLBACK;"), "1", user, password)
            bad(f"{user}: DELETE negado", "DELETE FROM inscricoes_atividade WHERE id_participante=6 AND id_atividade=1;", 1142, user, password)
            bad(f"{user}: UPDATE em outra coluna negado", "UPDATE inscricoes_atividade SET data_inscricao=NULL WHERE id_participante=6 AND id_atividade=1;", 1143, user, password)
            bad(f"{user}: INSERT negado", "INSERT INTO pessoa(nome,email) VALUES('Teste','teste@example.com');", 1142, user, password)

        good("Uma procedure, uma function, uma view e um trigger", f"SELECT routine_type,COUNT(*) FROM information_schema.routines WHERE routine_schema='{DB}' GROUP BY routine_type ORDER BY routine_type; SELECT COUNT(*) FROM information_schema.views WHERE table_schema='{DB}'; SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='{DB}';", "FUNCTION\t1\nPROCEDURE\t1\n1\n1")
        if hashlib.sha256((ROOT / "segundaEntrega.drawio").read_bytes()).hexdigest() != diagram_hash:
            raise AssertionError("O arquivo Draw.io foi alterado durante a validacao.")
        checks.append("Arquivo Draw.io preservado durante a validacao")

        # O encerramento e conferido antes de emitir o relatorio de sucesso.
        shutdown = subprocess.run(
            [str(admin_exe), "--no-defaults", "--protocol=TCP", "--host=127.0.0.1",
             f"--port={port}", "--user=root", "shutdown"],
            capture_output=True, timeout=20, creationflags=HIDDEN,
        )
        server.wait(timeout=25)
        if shutdown.returncode or server.returncode:
            raise RuntimeError("Nao foi possivel confirmar encerramento normal do servidor temporario.")
        stopped = True
        report = [
            "# Validação da segunda entrega", "",
            f"Executada em {run_date}, usando os scripts entregues.", "",
            f"**Resultado: {len(checks)} verificações aprovadas em MySQL {version}.**", "",
            "Ambiente: instância temporária, com dados próprios, conectada somente em 127.0.0.1 e em porta temporária. O diretório de dados da conexão foi conferido antes da execução dos scripts. Os bancos, usuários e serviços MySQL existentes do estudante não foram utilizados.", "",
            "Os dois usuários de demonstração foram criados e testados exclusivamente nessa instância. O servidor temporário foi encerrado após os testes. Nenhum software foi instalado.", "",
            "## Contagens finais", "", "| Tabela | Registros |", "| --- | ---: |",
        ]
        report.extend(f"| `{line.split(chr(9))[0]}` | {line.split(chr(9))[1]} |" for line in counts.splitlines())
        report.extend(["", "## Verificações", ""])
        report.extend(f"{index}. {label}." for index, label in enumerate(checks, 1))
        report.extend([
            "", "## Evidências e limites", "",
            "A saída completa das consultas do script principal está em `saida_script_principal.txt`. Os cenários de mutação adicionais usam ROLLBACK quando necessário, preservando os resultados demonstrados no script.", "",
            "O confronto automático com o Draw.io verifica as sete tabelas, nomes e ordem das colunas, tipos, nulabilidade, defaults, AUTO_INCREMENT, PKs, UNIQUEs e vínculos de FKs. BOOLEAN é comparado com sua representação tinyint(1) no MySQL. As ações referenciais foram conferidas com o SQL anterior e com os comportamentos de CASCADE e SET NULL.", "",
            "As consultas Q1 a Q6 são extraídas do próprio script entregue e seus resultados completos são comparados com os resultados esperados da carga fictícia. Os dois diagramas foram comparados por entidades, atributos, cardinalidades e vínculos. Três notas explicativas presentes apenas no arquivo anterior foram identificadas e desconsideradas nessa comparação estrutural; os arquivos e sua disposição visual não precisam ser idênticos.", "",
            "Isso comprova execução local dos scripts e dos casos listados. Não comprova execução na conexão habitual do estudante, configuração de outro servidor, testes de carga ou aceitação pelo professor.", "",
            f"SHA-256 do Draw.io preservado: `{diagram_hash}`.", "",
        ])
        (OUT / "VALIDACAO.md").write_text("\n".join(report), encoding="utf-8")
        print(f"CONCLUIDO: {len(checks)} verificacoes aprovadas; servidor temporario encerrado.", flush=True)
    finally:
        # No Windows, encerrar apenas o processo inicial pode deixar um filho
        # mysqld ativo. Em falhas, tentar primeiro o encerramento SQL da instancia
        # cuja identidade e conferida pelo datadir, mesmo se o processo inicial saiu.
        if server is not None and not stopped:
            try:
                cleanup_probe = run_sql("SELECT @@datadir;")
                if cleanup_probe.returncode == 0 and Path(cleanup_probe.stdout.strip()).resolve() == data.resolve():
                    subprocess.run(
                        [str(admin_exe), "--no-defaults", "--protocol=TCP", "--host=127.0.0.1",
                         f"--port={port}", "--user=root", "shutdown"],
                        capture_output=True, timeout=20, creationflags=HIDDEN,
                    )
                    if server.poll() is None:
                        server.wait(timeout=25)
            except (OSError, subprocess.SubprocessError) as cleanup_error:
                print(f"Conferir encerramento da instancia temporaria: {cleanup_error}", flush=True)
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=20)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=10)
        if log_file is not None:
            log_file.close()
        # Somente o diretorio criado por esta execucao, dentro do Temp, e removido.
        if stopped:
            temp_root = Path(tempfile.gettempdir()).resolve()
            resolved_workspace = workspace.resolve()
            if resolved_workspace.parent != temp_root or not resolved_workspace.name.startswith("c07_segunda_entrega_"):
                raise RuntimeError("Diretorio inesperado; limpeza cancelada.")
            shutil.rmtree(resolved_workspace)
        else:
            print(f"Logs mantidos para diagnostico: {workspace}", flush=True)


if __name__ == "__main__":
    main()
