from pathlib import Path
import os
import shutil
import subprocess,json,re,xml.etree.ElementTree as E
BASE=Path(__file__).resolve().parents[1]
MYSQL = os.getenv('C07_MYSQL_CLIENT') or shutil.which('mysql') or r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe'
PORTA = int(os.getenv('C07_MYSQL_TEST_PORT', '33079'))
DATADIR = Path(os.environ['C07_MYSQL_TEST_DATADIR']).resolve()
ARGS = [MYSQL, '--no-defaults', '--protocol=tcp', '--host=127.0.0.1', f'--port={PORTA}',
        '--user=root', '--default-character-set=utf8mb4', '--batch', '--raw', '--skip-column-names']
results=[]
def query(sql):
 return subprocess.run(ARGS,input=sql.encode('utf-8'),capture_output=True,timeout=25)
def ok(name,sql,expected=None):
 r=query('USE festival_inovacao;\n'+sql)
 assert r.returncode==0,(name,r.stderr.decode('utf-8',errors='replace'))
 out=r.stdout.decode('utf-8').replace('\r\n','\n').strip()
 if expected is not None:assert out==expected,(name,out,expected)
 results.append({'teste':name,'resultado':'PASSOU'})
def fails(name,sql,code):
 r=query('USE festival_inovacao;\n'+sql)
 assert r.returncode!=0 and ('ERROR '+str(code)).encode() in r.stderr,(name,r.stdout,r.stderr)
 results.append({'teste':name,'resultado':'PASSOU','erro_esperado':code})
source = (BASE / 'trabalho_C07.sql').read_text(encoding='utf-8')
identity = query('SELECT @@port, @@datadir, VERSION();')
if identity.returncode:
    raise RuntimeError(identity.stderr.decode('utf-8', errors='replace'))
port, directory, version = identity.stdout.decode('utf-8').strip().split('\t')
if int(port) != PORTA or Path(directory).resolve() != DATADIR:
    raise RuntimeError('A conexao nao corresponde a instancia isolada indicada.')
existing = query("SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name='festival_inovacao';")
if existing.returncode or existing.stdout.strip() != b'0':
    raise RuntimeError('Use uma instancia isolada sem o banco festival_inovacao.')
r = query(source)
assert r.returncode == 0, r.stderr.decode('utf-8', errors='replace')
results.append({'teste': f'Criacao integral do SQL no MySQL {version}', 'resultado': 'PASSOU'})
ok('Sete tabelas criadas',"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='festival_inovacao';",'7')
ok('Carga de pessoas e especializacoes',"""
INSERT INTO pessoa(id_pessoa,nome,email) VALUES (1,'Ana','ana@example.test'),(2,'Beto','beto@example.test'),(3,'Caio','caio@example.test'),(4,'Dora','dora@example.test');
INSERT INTO participante VALUES (1,'Inteira'),(3,'Meia'),(4,'Inteira');
INSERT INTO palestrante(id_pessoa,area_especialidade) VALUES (2,'Banco de dados'),(4,'Software');
""")
fails('Heranca impede subclasse sem Pessoa',"INSERT INTO participante VALUES (999,'Inteira');",1452)
fails('Email unico preservado',"INSERT INTO pessoa(nome,email) VALUES ('Outra Ana','ana@example.test');",1062)
ok('1:N e recursividade aceitam varios dependentes',"""
INSERT INTO espaco VALUES (1,'Auditorio',100);
INSERT INTO atividade(id_atividade,titulo,data_hora_inicio,id_espaco,id_palestrante,id_atividade_prerequisito)
VALUES (1,'Introducao','2026-09-20 09:00:00',1,2,NULL),(2,'Pratica','2026-09-20 10:00:00',1,2,1),(3,'Debate','2026-09-20 11:00:00',1,2,1);
SELECT COUNT(*) FROM atividade WHERE id_atividade_prerequisito=1;
""",'2')
fails('Recursividade impede pre-requisito inexistente',"UPDATE atividade SET id_atividade_prerequisito=999 WHERE id_atividade=3;",1452)
ok('N:M aceita varios participantes e atividades',"""
INSERT INTO inscricoes_atividade(id_participante,id_atividade,data_inscricao) VALUES (1,1,'2026-09-17 19:00:00'),(1,2,'2026-09-17 19:00:00'),(3,1,'2026-09-17 19:00:00');
SELECT COUNT(*) FROM inscricoes_atividade;
""",'3')
fails('PK composta impede inscricao duplicada',"INSERT INTO inscricoes_atividade(id_participante,id_atividade) VALUES (1,1);",1062)
fails('Inscricao exige participante existente',"INSERT INTO inscricoes_atividade(id_participante,id_atividade) VALUES (999,1);",1452)
ok('Data opcional e checkin falso preservados',"INSERT INTO inscricoes_atividade(id_participante,id_atividade) VALUES (4,3); SELECT data_inscricao IS NULL,status_checkin FROM inscricoes_atividade WHERE id_participante=4;",'1\t0')
ok('Credenciais validas',"INSERT INTO credencial(codigo,id_participante) VALUES ('CRED-ANA',1),('CRED-CAIO',3);")
fails('1:1 impede segunda credencial do participante',"INSERT INTO credencial(codigo,id_participante) VALUES ('OUTRA-ANA',1);",1062)
fails('Credencial exige participante nao nulo',"INSERT INTO credencial(codigo,id_participante) VALUES ('SEM-PARTICIPANTE',NULL);",1048)
fails('Credencial exige participante existente',"INSERT INTO credencial(codigo,id_participante) VALUES ('INVALIDA',999);",1452)
fails('Codigo de credencial unico',"INSERT INTO credencial(codigo,id_participante) VALUES ('CRED-ANA',4);",1062)
ok('ON UPDATE CASCADE em heranca, inscricao e credencial',"UPDATE pessoa SET id_pessoa=30 WHERE id_pessoa=3; SELECT id_pessoa FROM participante WHERE id_pessoa=30; SELECT id_participante FROM credencial WHERE codigo='CRED-CAIO'; SELECT id_participante FROM inscricoes_atividade WHERE id_participante=30;",'30\n30\n30')
ok('Excluir espaco aplica SET NULL',"DELETE FROM espaco WHERE id_espaco=1; SELECT COUNT(*) FROM atividade WHERE id_espaco IS NULL;",'3')
ok('Excluir palestrante aplica SET NULL',"DELETE FROM palestrante WHERE id_pessoa=2; SELECT COUNT(*) FROM atividade WHERE id_palestrante IS NULL;",'3')
ok('Excluir pre-requisito aplica SET NULL e remove inscricoes vinculadas',"DELETE FROM atividade WHERE id_atividade=1; SELECT COUNT(*) FROM atividade WHERE id_atividade_prerequisito IS NULL; SELECT COUNT(*) FROM inscricoes_atividade WHERE id_atividade=1;",'2\n0')
ok('Excluir pessoa propaga para participante, credencial e inscricoes',"DELETE FROM pessoa WHERE id_pessoa=1; SELECT COUNT(*) FROM participante WHERE id_pessoa=1; SELECT COUNT(*) FROM credencial WHERE id_participante=1; SELECT COUNT(*) FROM inscricoes_atividade WHERE id_participante=1;",'0\n0\n0')

# Comparacao entre colunas reais e conteudo da pagina relacional do Draw.io.
r=query("SELECT TABLE_NAME,COLUMN_NAME FROM information_schema.columns WHERE table_schema='festival_inovacao' ORDER BY TABLE_NAME,ORDINAL_POSITION;")
assert r.returncode==0
actual={}
for line in r.stdout.decode().splitlines():
 table,col=line.split('\t');actual.setdefault(table,[]).append(col)
doc=E.parse(BASE/'Festival_corrigido.drawio')
root=doc.findall('./diagram')[1].find('./mxGraphModel/root')
for table,cols in actual.items():
 body=root.find(f"mxCell[@id='{table}_rows']")
 assert body is not None,table
 diagram_cols=[line.split(' ')[0] for line in body.get('value').splitlines()]
 assert diagram_cols==cols,(table,cols,diagram_cols)
results.append({'teste':'Colunas do modelo relacional correspondem as sete tabelas executadas','resultado':'PASSOU'})
output = BASE / 'validacao' / 'gerados'
output.mkdir(exist_ok=True)
report = {'mysql': version, 'ambiente': f'Instancia isolada em TCP 127.0.0.1:{PORTA}', 'testes': results}
(output / 'validacao_mysql.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(results)} verificacoes passaram no MySQL {version} e na comparacao com o Draw.io.')
