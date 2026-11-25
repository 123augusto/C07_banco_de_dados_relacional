# Revisão da segunda entrega — C07

Data: **28/10/2026**. Alvo: **MySQL 8.0 ou superior**. Execução verificada: **MySQL 8.0.46**.

## Resultado da revisão

**Os requisitos transcritos do professor estão cobertos pelos dois scripts SQL e pela documentação. Não foram encontradas divergências estruturais entre a implementação e o diagrama recebido.**

A execução revisada passou em **65 verificações automatizadas**, incluindo o confronto completo da estrutura com o Draw.io e dos resultados das consultas Q1 a Q6. Os testes foram executados em uma instância temporária, encerrada após a validação. O relatório detalhado está em `VALIDACAO.md`.

**Revisão manual do estudante: pendente.** Este relatório registra a conferência técnica e documental, sem presumir aceitação pelo professor.

## 1. Fontes e escopo

- Enunciado: os requisitos da segunda entrega transcritos pelo estudante nesta conversa.
- Modelo principal: `segundaEntrega/segundaEntrega.drawio`, com as páginas conceitual e relacional.
- Modelo anterior de apoio: `../entrega_01/Festival_corrigido.drawio`.
- SQL anterior de apoio: `../entrega_01/trabalho_C07.sql`, especialmente as ações referenciais das FKs.
- Implementação revisada: `segundaEntrega.sql` e `usuarios_roles.sql`.
- Texto revisado: comentários dos scripts, `DOCUMENTACAO.md`, relatório de validação e resultados das consultas.
- Materiais didáticos: os materiais já reunidos no projeto, incluindo a apostila e as aulas de DCL, TCL, DQL e Objetos Programáveis incorporadas à pasta `Lab`.

O atendimento ao enunciado considera **os dois scripts SQL**. O principal contém estrutura, dados, DML, consultas e objetos; o segundo contém usuários, ROLE e permissões. Eles podem compor um arquivo único, preservando essa ordem, mas continuam separados nesta versão.

## 2. Conferência de cada requisito do professor

| Pedido | Evidência na entrega | Resultado |
| --- | --- | --- |
| Implementar o banco e as tabelas do modelo anterior | Seção 1 do principal; sete tabelas e 27 campos comparados com a página relacional do Draw.io. | Atendido. |
| Inserir pelo menos cinco registros em cada tabela | Seção 3 e contagem ao final da seção 8; valores conferidos após as demonstrações. | Atendido em todas as sete tabelas. |
| Usar DML e explicar os motivos | INSERT, UPDATE e DELETE na seção 6; comentários e seção 4 da documentação justificam cadastro, correção e cancelamento. | Atendido. |
| Implementar a herança do modelo | `palestrante.id_pessoa` e `participante.id_pessoa` são PKs e FKs para `pessoa.id_pessoa`. | Atendido. |
| Criar dois usuários relacionados por uma ROLE | `recepcao_ana`, `recepcao_bruno` e `r_recepcao_festival` em `usuarios_roles.sql`; associação e ativação padrão conferidas. | Atendido. |
| Consultas com JOIN sobre 1:1, 1:N e N:M | Q1 demonstra 1:1; Q2 demonstra 1:N; Q3 demonstra N:M; Q4 combina os três. | Atendido. |
| Criar ao menos uma Procedure e justificar | `sp_registrar_checkin`; seção 5 da documentação descreve a centralização do registro de presença. | Atendido. |
| Criar ao menos uma View e justificar | `vw_resumo_atividades`; seção 5 descreve a reutilização do relatório. | Atendido. |
| Criar ao menos um Trigger e justificar | `trg_inscricao_data`; seção 5 descreve o preenchimento de data ausente. | Atendido. |
| Criar ao menos uma Function e justificar | `fn_percentual_presenca`; seção 5 descreve o cálculo reutilizável do percentual. | Atendido. |
| Documentar implementações extras, caso existam | Seção 8 da documentação: autorrelacionamento, anti-join, percentual, transações, permissão por coluna e demonstração do trigger. | Extras documentados; eventual pontuação depende do professor. |

O enunciado fornecido define as cardinalidades 1:1, 1:N e N:M. Não estabelece quantidade mínima de JOINs por consulta nem uma métrica formal de complexidade. A entrega utiliza múltiplas tabelas, agregações, GROUP BY, HAVING e subconsultas, além dos JOINs exigidos.

## 3. Fidelidade ao diagrama anterior

### Estrutura

Foram conferidas **sete tabelas, 27 campos, sete PKs, oito FKs, três restrições UNIQUE adicionais às PKs e quatro identificadores AUTO_INCREMENT**. Os tipos, tamanhos de VARCHAR, obrigatoriedade dos campos e DEFAULT FALSE de `status_checkin` correspondem ao Draw.io. No MySQL, BOOLEAN aparece nos metadados como `tinyint(1)`.

| Elemento do modelo | Implementação preservada |
| --- | --- |
| Pessoa como superclasse | Dados comuns permanecem exclusivamente na tabela `pessoa`. |
| Palestrante e Participante como subclasses | Mesmo `id_pessoa` como PK/FK; sem identificador independente nas subclasses. |
| Participante–Credencial: máximo 1:1 | FK obrigatória e UNIQUE em `credencial.id_participante`; participante pode permanecer sem credencial. |
| Palestrante–Atividade: 1:N | FK opcional em `atividade.id_palestrante`; um palestrante pode ministrar várias atividades. |
| Espaço–Atividade: 1:N | FK opcional em `atividade.id_espaco`; um espaço pode sediar várias atividades. |
| Participante–Atividade: N:M | `inscricoes_atividade`, com PK composta por participante e atividade. |
| Pré-requisito recursivo de Atividade | FK opcional para a própria tabela; até um pré-requisito por atividade e possibilidade de várias atividades dependentes. |

As ações de exclusão e atualização seguem o SQL anterior: CASCADE nas dependências de pessoa/participante e SET NULL nas referências opcionais de atividade; as FKs mantêm ON UPDATE CASCADE. Os nomes das constraints podem diferir sem alterar os vínculos.

### Diferença entre os dois arquivos Draw.io

Os arquivos não são idênticos. O modelo anterior contém três notas explicativas que não constam no arquivo recebido para esta entrega: duas notas de legenda e uma anotação que nomeia a tabela intermediária. As entidades, os atributos, as cardinalidades e os vínculos comparados permanecem equivalentes. A tabela intermediária também está explicitada na página relacional do arquivo recebido.

Essas notas foram identificadas e excluídas apenas da comparação estrutural automática. **Nenhum dos diagramas foi alterado.** A comparação não é uma aprovação da disposição visual ou da legibilidade do desenho.

### Comportamento acrescentado nesta entrega

O trigger preenche a data quando uma nova inscrição é inserida sem esse valor. Isso é uma automação proposta para cumprir o requisito de objeto programável e está documentado. A coluna mantém o tipo e a nulabilidade do diagrama; o preenchimento não cria uma nova coluna nem muda os relacionamentos.

O diagrama não determina exclusividade ou cobertura total das subclasses. A implementação permite sobreposição entre Participante e Palestrante e a existência de Pessoa sem subclasse. Esses comportamentos foram testados.

## 4. Registros conferidos

| Tabela | Quantidade após o script completo |
| --- | ---: |
| `pessoa` | 11 |
| `palestrante` | 5 |
| `participante` | 6 |
| `espaco` | 5 |
| `atividade` | 6 |
| `inscricoes_atividade` | 16 |
| `credencial` | 5 |

A inscrição criada para demonstrar DELETE é removida na própria demonstração. A inscrição criada para demonstrar o trigger é desfeita com ROLLBACK. As quantidades acima permanecem válidas ao final do arquivo.

## 5. Consistência entre texto e código

- A documentação descreve os objetos atuais: um trigger, uma procedure, uma function e uma view.
- A procedure informa inscrição inexistente por mensagem, sem lançar uma exceção SQL e sem criar inscrição.
- A function calcula o percentual com parâmetros; a view fornece os totais. A coluna de percentual pertence à consulta final que combina os dois objetos.
- Na Q1, a ausência de credencial aparece como NULL. Na Q2, espaço sem atividade tem contagem zero e soma de minutos NULL. O texto acompanha esses resultados.
- A demonstração final do trigger foi acrescentada ao SQL, com ROLLBACK, para que seu efeito também possa ser observado no arquivo entregue.
- O relatório de validação foi atualizado para a nova execução e ampliado para comparar os resultados integrais das seis consultas.
- Os padrões de caracteres e comparação são herdados do servidor, pois não há CHARACTER SET ou COLLATE explícitos no principal.
- A presença dos recursos nas aulas está referenciada na documentação. A lógica específica do festival e as concessões necessárias à execução das rotinas são escolhas da implementação, identificadas como tais.

## 6. Limites mantidos

O enunciado e o modelo fornecidos não especificam proibição de conflitos de horário, controle automático de lotação, proibição de ciclos entre pré-requisitos ou verificação da conclusão de pré-requisitos. Essas regras não foram acrescentadas como se fossem exigências do professor.

A function é utilizada com totais de contagem produzidos pelo relatório; não foi apresentada como um validador de entradas arbitrárias. O perfil de recepção foi criado para demonstrar permissões na disciplina. A execução em outra configuração de servidor e a aceitação acadêmica continuam sujeitas à conferência do estudante e do professor.

## 7. Sua revisão manual

Marque somente depois da sua conferência:

- [ ] Conferi as sete tabelas e seus campos com o Draw.io.
- [ ] Conferi a herança Pessoa → Palestrante/Participante.
- [ ] Conferi os relacionamentos 1:1, 1:N, N:M e o recursivo.
- [ ] Conferi a quantidade mínima de registros em cada tabela.
- [ ] Conferi os exemplos de INSERT, UPDATE e DELETE e suas justificativas.
- [ ] Conferi a Procedure, a View, o Trigger e a Function com as justificativas.
- [ ] Conferi as consultas Q1 a Q6 e os resultados apresentados.
- [ ] Conferi os dois usuários, a ROLE e as permissões.
- [ ] Conferi os extras descritos na documentação.
- [ ] Conferi se os arquivos que vou entregar contêm os dois scripts completos e a documentação exigida.

O ponto inicial para essa conferência é a **seção 1 de `segundaEntrega.sql`**, junto à página relacional do Draw.io. As explicações de uso de cada trecho ficam para quando forem solicitadas.
