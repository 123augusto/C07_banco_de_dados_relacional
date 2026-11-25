# Segunda entrega — Festival de Inovação

Versão preparada em 27/10/2026 para **MySQL 8.0 ou superior**, conforme confirmado pelo estudante. Os scripts foram testados no MySQL 8.0.46. Os nomes, contatos, datas e inscrições utilizados são fictícios.

Revisão de conformidade realizada em **28/10/2026**, com **65 verificações aprovadas** em instância temporária do MySQL 8.0.46. O resultado e o roteiro de conferência do estudante estão em `REVISAO_PARA_CONFERENCIA_MANUAL.md`. A revisão manual do estudante permanece pendente.

Revisão alinhada às aulas recebidas em 27/10/2026. A criação do banco usa a forma básica apresentada nas aulas; os objetos programáveis foram simplificados com base na Aula 09. A lógica específica do festival é uma proposta de aplicação desses recursos, e não uma reprodução literal dos exemplos dos slides.

## 1. Arquivos e execução

| Arquivo | Finalidade |
| --- | --- |
| `segundaEntrega.drawio` | Modelo conceitual e relacional recebido; referência para a estrutura. |
| `segundaEntrega.sql` | Cria o banco e as sete tabelas; cria os objetos; insere os dados; demonstra DML e consultas. |
| `usuarios_roles.sql` | Cria dois usuários e uma ROLE, concede permissões e demonstra as concessões. |
| `VALIDACAO.md` | Registra os resultados dos testes em ambiente temporário. |
| `REVISAO_PARA_CONFERENCIA_MANUAL.md` | Consolida a comparação com o diagrama e o enunciado e reserva uma lista para a revisão manual do estudante. |

Ordem recomendada no MySQL Workbench:

1. Abra uma conexão com uma conta que possa criar banco, tabelas, rotinas, triggers e views.
2. Abra `segundaEntrega.sql` e execute o arquivo completo uma única vez.
3. Confira as consultas apresentadas ao final, especialmente a contagem de registros.
4. Abra e execute `usuarios_roles.sql` com uma conta administradora autorizada a criar usuários/roles e conceder os privilégios utilizados.
5. Abra uma nova conexão para cada usuário e execute os exemplos de conferência indicados no final desse arquivo.

O banco criado recebe o nome `festival_inovacao_segunda_entrega`. Esse nome separa a entrega do banco anterior `festival_inovacao`. Os scripts criam uma instalação nova: não são migrações e não devem ser executados novamente sobre uma instalação já preenchida. Se aparecer erro de banco, tabela ou usuário existente, interrompa a execução e confira o ambiente antes de prosseguir. Os arquivos não contêm comandos para apagar bancos ou contas existentes.

O script de usuários solicita senhas aleatórias ao MySQL. Guarde as senhas retornadas para conectar com as contas de recepção.

`DELIMITER` indica ao Workbench ou cliente MySQL como separar os comandos com `BEGIN ... END`. Ele permite que os pontos e vírgulas internos das rotinas sejam interpretados corretamente. Não é uma instrução executada pelo servidor. [Referência oficial sobre programas armazenados](https://dev.mysql.com/doc/refman/8.0/en/stored-programs-defining.html).

## 2. Conferência do enunciado

| Exigência | Implementação |
| --- | --- |
| Banco e tabelas do modelo anterior | Seção 1 de `segundaEntrega.sql`: sete tabelas, com colunas, tipos, PKs, FKs e opcionalidades do Draw.io. |
| Mínimo de cinco registros por tabela | Seção 3; a consulta final comprova as quantidades após a demonstração de DML. |
| DML e justificativas | Seção 6: cadastrar inscrição, corrigir telefone e cancelar inscrição. |
| Herança | `pessoa` é a superclasse; `palestrante` e `participante` reutilizam `id_pessoa` como PK/FK. |
| Dois usuários relacionados por uma ROLE | `recepcao_ana` e `recepcao_bruno` recebem `r_recepcao_festival`. |
| JOIN em 1:1 | Q1: participante e credencial, recuperando o nome em pessoa. |
| JOIN em 1:N | Q2: espaços e respectivas atividades; Q4 também relaciona palestrante e atividade. |
| JOIN em N:M | Q3: participante, inscrição e atividade. |
| Consulta integrando os três relacionamentos | Q4: inscrições com nome, credencial, atividade, espaço e palestrante. |
| Procedure | `sp_registrar_checkin`: registra presença em uma inscrição existente. |
| View | `vw_resumo_atividades`: resume inscrições e presenças por atividade. |
| Trigger | `trg_inscricao_data`: preenche a data de inscrição quando não informada. |
| Function | `fn_percentual_presenca`: calcula a porcentagem de presença a partir dos totais recebidos. |
| Extras documentados | JOIN recursivo, anti-join, percentuais e uso de transações. |

**Cardinalidade e tipo de JOIN são conceitos distintos.** As expressões 1:1, 1:N e N:M descrevem os relacionamentos do modelo. `INNER JOIN` e `LEFT JOIN` definem quais linhas serão mostradas na consulta. O enunciado transcrito exige consultas sobre as três cardinalidades; não informa que sejam obrigatórios três tipos diferentes de JOIN.

## 3. Estrutura preservada do modelo

| Tabela | Conteúdo | Quantidade final prevista |
| --- | --- | ---: |
| `pessoa` | Nome, e-mail e telefone comuns às subclasses. | 11 |
| `palestrante` | Minicurrículo e área de especialidade. | 5 |
| `participante` | Tipo de ingresso. | 6 |
| `espaco` | Local e capacidade máxima. | 5 |
| `atividade` | Programação, espaço, palestrante e possível pré-requisito. | 6 |
| `inscricoes_atividade` | Associação N:M, data de inscrição e check-in. | 16 |
| `credencial` | Código e vínculo exclusivo com participante. | 5 |

Um registro da superclasse e um da subclasse representam a mesma pessoa em duas tabelas. Não é necessário que `pessoa`, `palestrante` e `participante` tenham quantidades iguais. Cada tabela precisa atender individualmente ao mínimo do enunciado.

### Herança

Exemplo: a pessoa de identificador 1 tem nome e e-mail em `pessoa`; sua área de especialidade está em `palestrante`, também com identificador 1. A consulta com JOIN reúne esses atributos.

```sql
SELECT p.id_pessoa, p.nome, p.email, pal.area_especialidade
FROM pessoa AS p
INNER JOIN palestrante AS pal ON pal.id_pessoa = p.id_pessoa;
```

Não se cria outro identificador automático nas subclasses. A FK impede cadastrar um palestrante ou participante sem a pessoa correspondente. A PK impede repetir essa pessoa dentro da mesma subclasse. O mapeamento usa tabelas relacionadas: o MySQL não exige um comando chamado `INHERITS` para realizar essa estratégia.

O diagrama não impõe exclusividade nem cobertura total da especialização. Portanto, não se acrescentou uma proibição de a mesma pessoa ser participante e palestrante, nem uma obrigação de toda pessoa pertencer a uma subclasse.

### Relacionamentos e integridade

- **1:1:** `credencial.id_participante` tem FK, `NOT NULL` e `UNIQUE`. Toda credencial exige um participante existente; cada participante admite no máximo uma credencial. O participante pode não ter credencial.
- **1:N:** a FK fica em `atividade`, referenciando o espaço ou palestrante. As FKs aceitam NULL, conforme o modelo.
- **N:M:** a tabela `inscricoes_atividade` contém as duas FKs. A PK composta impede repetir o mesmo par participante–atividade, sem impedir outras combinações.
- **Recursivo:** `atividade.id_atividade_prerequisito` referencia `atividade.id_atividade`. O modelo admite no máximo um pré-requisito por atividade, e uma atividade pode ser pré-requisito de várias outras.

As ações referenciais seguem o SQL anterior consultado em `../entrega_01/trabalho_C07.sql`: `CASCADE` para as subclasses, inscrições e credenciais; `SET NULL` para referências opcionais da atividade. São escolhas de implementação compatíveis com as participações do diagrama. A estrutura também usa `ON UPDATE CASCADE`, preservando o SQL anterior; alterações de identificadores em referências recursivas têm restrições específicas do MySQL e não fazem parte da demonstração. [Referência oficial de FKs](https://dev.mysql.com/doc/refman/8.0/en/create-table-foreign-keys.html).

## 4. DML e motivos

`INSERT`, `UPDATE` e `DELETE` alteram os dados armazenados. `CREATE TABLE` define a estrutura. Nas explicações desta entrega, `SELECT` é apresentado como consulta/DQL.

| Comando | Situação demonstrada | Por que utilizar |
| --- | --- | --- |
| `INSERT INTO` | Carga inicial e inscrição temporária de Luiza na atividade 1. | Acrescentar registros que ainda não existem. |
| `UPDATE ... WHERE` | Corrigir o telefone da pessoa 6. | Corrigir um atributo mantendo a identidade e os relacionamentos da pessoa. |
| `DELETE ... WHERE` | Cancelar a inscrição `(11, 1)`. | Remover somente essa associação; Luiza continua cadastrada como participante. |

Os comandos da seção 6 são exemplos fictícios de operação. O INSERT é mostrado antes do DELETE; a exclusão retira apenas a inscrição criada nessa demonstração. Por isso, permanecem 16 inscrições e pelo menos cinco registros em todas as tabelas.

`WHERE` identifica o registro a atualizar ou excluir. Nesses exemplos, usa a PK simples ou composta, evitando alterar todos os registros da tabela. Não foi necessário desativar `SQL_SAFE_UPDATES`.

As cargas e a sequência de DML utilizam `START TRANSACTION` e `COMMIT`. `COMMIT` confirma as alterações. Em uma prática manual, `ROLLBACK` antes do COMMIT permite desfazer a transação. Isso não torna a criação de todo o banco reversível em um único ROLLBACK; comandos DDL do MySQL possuem regras próprias de confirmação.

## 5. Procedure, View, Trigger e Function

As finalidades abaixo são **propostas de implementação para cumprir a segunda entrega**. Não foram apresentadas como novas exigências do professor nem como regras já contidas no Draw.io.

### Procedure: `sp_registrar_checkin`

**Problema:** registrar a presença exige localizar a inscrição correta e atualizar seu status.

**Solução:** receber os identificadores do participante e da atividade e verificar a existência da inscrição com `IF EXISTS`. Quando ela existe, executar o UPDATE do check-in e apresentar `Check-in registrado.`. Quando não existe, apresentar `Inscricao nao encontrada.`, sem criar registros. Repetir a chamada de uma inscrição já confirmada mantém a presença marcada.

```sql
CALL sp_registrar_checkin(8, 1);
```

O procedimento não cria inscrição automaticamente, não exige credencial e não verifica a conclusão de pré-requisitos. Essas regras não estão especificadas no modelo. Ele também não inicia ou confirma uma transação própria; pode participar da transação aberta por quem o chama.

### View: `vw_resumo_atividades`

**Problema:** a organização precisa consultar repetidamente programação, locais, palestrantes, inscritos e presenças.

**Solução:** guardar a definição dessa consulta em uma view. O relatório é recalculado quando consultado, utilizando os dados então visíveis à consulta. `LEFT JOIN` mantém atividades ainda sem espaço, palestrante ou inscrições. `COUNT(i.id_participante)` retorna zero para uma atividade sem inscrições. Uma subconsulta correlacionada com `COUNT(*)` conta apenas os check-ins confirmados, também retornando zero quando não há presenças.

O percentual é calculado pela function na consulta final que utiliza essa view. A view contém os totais; a coluna de percentual pertence ao resultado dessa consulta final.

```sql
SELECT * FROM vw_resumo_atividades ORDER BY id_atividade;
```

### Trigger: `trg_inscricao_data`

**Problema:** uma nova inscrição pode ser cadastrada sem a data de registro.

**Solução proposta:** antes do INSERT, verificar `NEW.data_inscricao IS NULL`. Nesse caso, preencher o campo com `NOW()`. Uma data fornecida explicitamente é preservada. O gatilho combina `FOR EACH ROW`, `IF` e `SET NEW`, presentes na Aula 09, com `IS NULL`, apresentado na Aula 08; `NOW()` aparece no exemplo de auditoria da Aula 09, página 21.

Essa automação é uma proposta para a segunda entrega. A coluna mantém o tipo e a nulabilidade do modelo; o preenchimento acontece no INSERT pelo trigger, sem adicionar um DEFAULT à estrutura. Ele não altera datas de inscrições existentes nem preenche datas durante UPDATE.

`NEW` representa os valores da linha que será gravada. O gatilho é automático. A carga inicial informa todas as datas; a validação também testa novas inscrições com data ausente e com data explícita.

A seção 8 do SQL demonstra o gatilho com uma inscrição temporária de Luiza na atividade 6, omitindo a data. O SELECT mostra a data preenchida e o ROLLBACK desfaz essa inscrição, mantendo as quantidades finais previstas.

### Function: `fn_percentual_presenca`

**Problema:** reutilizar o cálculo do percentual de presença, incluindo a situação sem inscritos.

**Solução:** receber dois totais inteiros, na ordem check-ins e inscritos, e retornar `check-ins * 100 / inscritos` como `DECIMAL(5,2)`. Quando o total de inscritos é zero, retornar 0 para evitar divisão por zero. A conversão ao tipo de retorno apresenta duas casas decimais.

```sql
SELECT fn_percentual_presenca(3, 4); -- 75.00
SELECT fn_percentual_presenca(2, 3); -- 66.67
SELECT fn_percentual_presenca(0, 0); -- 0.00
```

A função usa parâmetros, `RETURNS`, `DETERMINISTIC`, `BEGIN`, `IF` e `RETURN`, combinando os recursos da Aula 09 com expressões aritméticas. Ela não consulta tabelas: os mesmos parâmetros produzem o mesmo resultado. Na consulta final, os parâmetros são os totais obtidos da view. Um parâmetro NULL produz NULL quando a operação aritmética é alcançada; com denominador zero, a função retorna 0. Os totais usados pelo relatório vêm de COUNT e não são nulos.

### Diferença entre os quatro objetos

| Objeto | Como é utilizado | Resultado neste projeto |
| --- | --- | --- |
| Procedure | `CALL nome(...)` | Executa a operação de check-in. |
| View | `SELECT ... FROM nome` | Apresenta um relatório reutilizável. |
| Trigger | Disparado pelo INSERT em inscrição | Preenche a data ausente antes da gravação. |
| Function | Dentro de uma expressão, como `SELECT nome(...)` | Devolve uma porcentagem. |

## 6. Usuários e ROLE

A ROLE `r_recepcao_festival` reúne permissões de um perfil de recepção. Os usuários `recepcao_ana` e `recepcao_bruno`, ambos limitados a conexões locais, recebem a mesma ROLE. Isso relaciona as duas contas por um conjunto comum de permissões; não exige criar tabelas de usuários do sistema dentro do modelo.

Permissões propostas para esse exercício:

- `SELECT` no banco do projeto, incluindo a view.
- `UPDATE` somente na coluna `status_checkin` de `inscricoes_atividade`.
- `EXECUTE` na procedure e na function criadas.

Esse perfil permite consultar dados e confirmar presenças, mas não permite INSERT, DELETE, criação de tabelas ou alteração de outras colunas. A consulta ao banco inteiro foi escolhida pela simplicidade do exercício; não representa um desenho de acesso a dados pessoais pronto para produção.

`GRANT` associa permissões à ROLE e associa a ROLE aos usuários. `SET DEFAULT ROLE` ativa esse perfil por padrão nas próximas conexões. Em uma conexão já aberta, pode ser necessário executar `SET ROLE DEFAULT` ou reconectar. `SHOW GRANTS` demonstra a concessão e `CURRENT_ROLE()` mostra a ativação na conexão. A ROLE representa um perfil de acesso; ela não é uma stored function. [Documentação oficial de roles](https://dev.mysql.com/doc/refman/8.0/en/roles.html).

As declarações dos objetos seguem a forma básica apresentada na Aula 09, sem cláusula explícita de segurança; mantêm o comportamento padrão do MySQL para execução com o definidor. A ROLE recebe EXECUTE para utilizar as duas rotinas e SELECT para consultar os dados. O GRANT de execução é o complemento de permissão necessário para que os exemplos funcionem nas contas criadas. A procedure recebe somente os identificadores e executa uma atualização fixa de check-in.

## 7. Como interpretar e apresentar as consultas

| Consulta | Pergunta respondida | Recursos principais | Resultado previsto após o script |
| --- | --- | --- | --- |
| Q1 — 1:1 | Quais participantes têm credencial e qual é o código? | INNER JOIN e LEFT JOIN. | 6 participantes; código NULL para Luiza, que não tem credencial. |
| Q2 — 1:N | Quantas atividades e quantos minutos estão programados por espaço? | LEFT JOIN, COUNT, SUM, GROUP BY e ORDER BY. | 5 espaços; auditório com 2 atividades; sala de apoio com 0 atividades e soma de minutos NULL. |
| Q3 — N:M | Quem tem pelo menos três inscrições e qual é sua carga de atividades? | Tabela associativa, múltiplos JOINs, agregações e HAVING. | 5 pessoas; João com 4 inscrições e as demais com 3. |
| Q4 — integrada | Quais participantes confirmaram presença, em qual atividade, com qual credencial, local e palestrante? | JOINs nos três relacionamentos, dois papéis para pessoa e filtro WHERE. | 6 presenças. |
| Q5 — recursiva | Quais atividades possuem pré-requisito e qual é ele? | JOIN da tabela atividade com ela própria, usando aliases. | Atividades 2 e 5 dependem da atividade 1. |
| Q6 — anti-join | Quem ainda não tem inscrição? | LEFT JOIN e IS NULL. | Luiza. |

`WHERE` filtra linhas antes do agrupamento; `HAVING` filtra os grupos depois de calcular as agregações. `AS` define apelidos para tornar a consulta legível. Na Q4, `pp` é a pessoa participante e `pl` é a pessoa palestrante: a mesma tabela é consultada em dois papéis diferentes.

Na consulta final que combina a view e a function, os resultados esperados são:

| Atividade | Inscritos | Check-ins | Presença |
| ---: | ---: | ---: | ---: |
| 1 | 4 | 3 | 75,00% |
| 2 | 3 | 0 | 0,00% |
| 3 | 3 | 2 | 66,67% |
| 4 | 3 | 0 | 0,00% |
| 5 | 3 | 1 | 33,33% |
| 6 | 0 | 0 | 0,00% |

Esses resultados pressupõem a execução integral do script uma única vez, sem outras alterações. Testes ou operações posteriores podem modificar os totais.

## 8. Extras e limites

| Extra implementado | Utilidade | Onde aparece |
| --- | --- | --- |
| Consulta de autorrelacionamento | Explora o pré-requisito já existente no modelo. | Q5. |
| Anti-join | Identifica participantes ainda sem inscrição. | Q6. |
| Percentual de presença | Facilita a leitura do relatório. | Function aplicada aos totais da view. |
| Transações explícitas | Agrupam a carga inicial e a sequência de DML. | Seções 3 e 6 do SQL. |
| Permissão por coluna | Limita o UPDATE da recepção ao check-in. | Script de usuários. |
| Demonstração do trigger com ROLLBACK | Mostra a automação sem alterar a carga final de dados. | Seção 8 do SQL. |
| Verificação de casos inválidos e comparação completa com o modelo | Evidencia a integridade, a fidelidade ao diagrama e os limites das permissões. | Relatório de validação. |

O modelo não especifica regras para impedir superlotação, conflitos de horário, ciclos de pré-requisitos ou inscrição antes da conclusão de um pré-requisito. Essas validações não foram acrescentadas como se fossem requisitos. `capacidade_maxima` é armazenada, mas não limita automaticamente a quantidade de inscrições. A FK recursiva comprova a existência do pré-requisito, sem impedir ciclos. `BOOLEAN` e as demais colunas anuláveis foram mantidos como no modelo, sem novas restrições CHECK.

Os extras não garantem pontuação adicional: a avaliação depende do professor. Os testes locais registrados em `VALIDACAO.md` não equivalem à execução na conexão do estudante nem à aceitação acadêmica.

## 9. Fontes utilizadas

### Complemento das aulas conferido em 27/10/2026

Após o recebimento das pastas das aulas 01 a 10, foram conferidos os PDFs e os exemplos relevantes nos originais. Cinco materiais novos diretamente relacionados à segunda entrega foram copiados para `Lab`, preservando seu conteúdo. As aulas 03 e 04 já existentes foram comparadas com as recebidas e são idênticas, inclusive o SQL `universidade.sql`. A pasta recebida `aula 10 - Integração` está vazia.

| Recurso | Evidência nos novos materiais |
| --- | --- |
| `DELIMITER` | Aula 09, `Objetos_Programaveis.pdf`, página 4: comparação de declaração de procedure com e sem delimitador personalizado. |
| `FOR EACH ROW` | Aula 09, página 16: estrutura do trigger; também aparece nos exemplos das páginas 18 e 19. |
| `NEW` e `SET NEW.campo = ...` | Aula 09, página 17: OLD/NEW; página 19: trigger BEFORE UPDATE alterando `NEW.total`. |
| `ENGINE=InnoDB` | Aula 01, `ApostilaC07.pdf`, página 5, seção 1.4.3: explicação e exemplo explícito na criação da tabela. |
| ROLE e associação aos usuários | Aula 06, `ComandosDCL.pdf`, páginas 9–14: CREATE ROLE, GRANT, CREATE USER e SET DEFAULT ROLE. |
| Transações | Aula 07, `ComandosTCL.pdf`: COMMIT, ROLLBACK e SAVEPOINT; página 19 contém exercício com START TRANSACTION. |
| `INNER JOIN` e `LEFT JOIN` | Aula 08, `Comandos_DQL.pdf`, páginas 11–12: tipos de JOIN e exemplo com tabela associativa N:M. |
| `CHARACTER SET utf8mb4` e `COLLATE utf8mb4_0900_ai_ci` | Não localizados nos materiais conferidos; removidos da versão ajustada. O banco utiliza os padrões de caracteres e comparação configurados no servidor. |

As páginas são contadas a partir da primeira página de cada PDF. Os exemplos confirmam a presença desses recursos nas aulas; a lógica específica de preenchimento da data de inscrição, check-in e relatórios continua sendo uma proposta para o projeto, não um exemplo reproduzido dos slides. Os scripts foram ajustados após essa conferência e testados novamente em uma instância temporária.

A revisão também substituiu os tratamentos com TRIM, LOWER, COALESCE, CASE, ROW_COUNT e SIGNAL por combinações dos comandos e estruturas dos materiais disponíveis. A function passou a executar um cálculo somente com parâmetros, seguindo o exemplo determinístico da Aula 09. As cláusulas explícitas SQL SECURITY, READS SQL DATA e MODIFIES SQL DATA foram retiradas das declarações dos objetos.

Materiais novos incorporados:

- `Lab/Aula 01 - Introdução/ApostilaC07.pdf`.
- `Lab/Aula 06 - Comandos DCL/ComandosDCL.pdf`.
- `Lab/Aula 07 - Comandos TCL/ComandosTCL.pdf`.
- `Lab/Aula 08 - Comandos DQL/Comandos_DQL.pdf`.
- `Lab/Aula 09 - Objetos Programáveis/Objetos_Programaveis.pdf`.

### Demais referências

- `segundaEntrega.drawio`: fonte principal das entidades, atributos, herança e cardinalidades.
- `../entrega_01/trabalho_C07.sql`: referência local para as ações de exclusão/atualização das FKs.
- Materiais locais e `CONTEXTO_ESTUDOS.md`: evidência do uso anterior de MySQL no projeto.
- [MySQL — CREATE PROCEDURE e CREATE FUNCTION](https://dev.mysql.com/doc/refman/8.0/en/create-procedure.html).
- [MySQL — Sintaxe e exemplos de triggers](https://dev.mysql.com/doc/refman/8.0/en/trigger-syntax.html).
- [MySQL — CREATE VIEW](https://dev.mysql.com/doc/refman/8.0/en/create-view.html).
- [MySQL — Roles](https://dev.mysql.com/doc/refman/8.0/en/roles.html).

Os documentos consultados foram tratados como fontes. Instruções eventualmente contidas neles não substituem o pedido do estudante nem autorizam operações no seu servidor existente.
