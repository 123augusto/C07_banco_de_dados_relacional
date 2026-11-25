# Festival de Inovação do Inatel — C07

O sistema organiza pessoas, palestrantes, participantes, espaços, atividades, inscrições e credenciais de um festival com palestras, oficinas e mesas-redondas.

## Integrantes

| Nome | Matrícula | Turma |
| --- | --- | --- |
| Augusto Leite Del' Carlo Carneiro | 866 | L1 |
| Vitor Augusto do Couto | 536 | L2 |

## Entregas

| Etapa | Arquivos |
| --- | --- |
| 1. Modelagem | [Modelo conceitual e relacional em Draw.io](entrega_01/Festival_corrigido.drawio), [script inicial](entrega_01/trabalho_C07.sql) e [modelo do Workbench](entrega_01/esse_vai_agora_final.mwb), acompanhado do [SQL exportado](entrega_01/esse_vai.sql). |
| 2. SQL | [Modelo e documentação da segunda entrega](entrega_02/README.md), incluindo carga de dados, rotinas, consultas e permissões de recepção. |
| 3. Integração | [Script SQL final](entrega_03/festival_final.sql), [conta da aplicação](entrega_03/usuario_aplicacao.sql) e [menu interativo em Python](entrega_03/main.py). |

## Executar a aplicação

1. Com o **MySQL Server 8.0.18 ou superior** em execução, abra `entrega_03/festival_final.sql` no MySQL Workbench e execute o arquivo completo com uma conta administradora. Isso cria o banco `festival_inovacao_final`, carrega dados fictícios e instala o trigger, a procedure, a function e a view. Execute o script uma vez para inicializar o banco.
2. Execute `entrega_03/usuario_aplicacao.sql` na mesma conexão. Guarde a senha gerada para a conta `festival_app@127.0.0.1`, que recebe as permissões de CRUD no banco do festival.
3. Na pasta raiz do repositório, execute os comandos abaixo com **Python 3.10 ou superior**. Informe a senha gerada quando o programa pedir.

```bash
python -m pip install -r entrega_03/requirements.txt
python entrega_03/main.py
```

Por padrão, a aplicação usa `festival_app` em `127.0.0.1:3306` com o banco `festival_inovacao_final`. Para especificar outra conexão local, use as variáveis de ambiente `C07_DB_USER`, `C07_DB_PORT` ou `C07_DB_NAME`. Também é possível definir `C07_DB_HOST` e `C07_DB_PASSWORD`. A senha pode ser digitada no terminal sem aparecer na tela.

## Demonstrar no menu

| Requisito | Como demonstrar |
| --- | --- |
| CRUD de todas as entidades | Abra qualquer opção de **1** a **7**. O submenu contém cadastro, listagem geral, busca por filtro, atualização e exclusão. |
| Busca por filtro | Escolha um atributo e informe o valor exato. Em um atributo opcional, use `:nulo` para encontrar registros com `NULL`. |
| Atualização com ou sem filtro | Escolha o atributo e o novo valor. Em seguida, escolha **Aplicar filtro** ou **Todos os registros**. A atualização geral pede que você digite `TODOS`. |
| Exclusão por filtro | Informe a chave primária e confirme com `SIM`. Para uma inscrição, informe o ID do participante e o ID da atividade. |
| JOIN 1:1 | Em **8 → 1**, consulte os participantes e suas credenciais. A carga inclui Luiza, que aparece mesmo sem credencial. |
| JOIN 1:N | Em **8 → 2**, consulte a quantidade de atividades por espaço. A Sala de apoio aparece com zero atividades. |
| JOIN N:M | Em **8 → 3**, consulte cada par de participante e atividade, com data de inscrição e situação do check-in. |

### Regras mantidas do banco

- Cadastre uma **Pessoa** antes de vinculá-la como **Participante** ou **Palestrante**. Use o `id_pessoa` na subclasse e edite nome, e-mail ou telefone no menu de Pessoas.
- As chaves primárias identificam os registros e são usadas nos filtros. Os demais atributos podem ser editados. Para trocar o participante ou a atividade de uma inscrição, exclua a inscrição anterior pela chave composta e cadastre a nova.
- Nas inscrições, pressione Enter no campo `data_inscricao` para que o trigger preencha a data. No campo `status_checkin`, `0` significa pendente e `1` significa confirmado.
- As exclusões seguem as regras já definidas nas chaves estrangeiras. Por exemplo, excluir um participante também exclui suas inscrições e sua credencial. Excluir um espaço mantém suas atividades e remove o vínculo com o espaço.

## Código de validação

- [Validação da modelagem](entrega_01/validacao/README.md) para reproduzir a revisão dos diagramas e conferir o primeiro SQL.
- [Validação da segunda entrega](entrega_02/VALIDACAO.md) com o relatório de referência e o script utilizado.
- [Validação do menu](entrega_03/validacao/validar_menu.py) com SQLite em memória. Rode `python entrega_03/validacao/validar_menu.py` com Python 3.10 ou superior.
- [Teste de integração](entrega_03/validacao/validar_mysql.py) executado pelo [GitHub Actions](.github/workflows/validar-mysql.yml) em uma instância temporária do MySQL 8.
