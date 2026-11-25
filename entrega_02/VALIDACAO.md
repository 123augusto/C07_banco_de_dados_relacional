# Validação da segunda entrega

Executada em 28/10/2026, usando os scripts entregues.

**Resultado: 65 verificações aprovadas em MySQL 8.0.46.**

Ambiente: instância temporária, com dados próprios, conectada somente em 127.0.0.1 e em porta temporária. O diretório de dados da conexão foi conferido antes da execução dos scripts. Os bancos, usuários e serviços MySQL existentes do estudante não foram utilizados.

Os dois usuários de demonstração foram criados e testados exclusivamente nessa instância. O servidor temporário foi encerrado após os testes. Nenhum software foi instalado.

## Contagens finais

| Tabela | Registros |
| --- | ---: |
| `atividade` | 6 |
| `credencial` | 5 |
| `espaco` | 5 |
| `inscricoes_atividade` | 16 |
| `palestrante` | 5 |
| `participante` | 6 |
| `pessoa` | 11 |

## Verificações

1. Servidor temporario identificado.
2. Script principal executado integralmente.
3. Script de dois usuarios e ROLE executado.
4. Minimo de cinco registros em cada uma das sete tabelas.
5. Diagrama recebido preserva entidades, atributos, cardinalidades e vinculos anteriores.
6. Exatamente as sete tabelas previstas no diagrama.
7. pessoa: colunas, tipos, nulabilidade, defaults e AUTO_INCREMENT conforme o Draw.io.
8. pessoa: chave primaria conforme o Draw.io.
9. palestrante: colunas, tipos, nulabilidade, defaults e AUTO_INCREMENT conforme o Draw.io.
10. palestrante: chave primaria conforme o Draw.io.
11. participante: colunas, tipos, nulabilidade, defaults e AUTO_INCREMENT conforme o Draw.io.
12. participante: chave primaria conforme o Draw.io.
13. atividade: colunas, tipos, nulabilidade, defaults e AUTO_INCREMENT conforme o Draw.io.
14. atividade: chave primaria conforme o Draw.io.
15. espaco: colunas, tipos, nulabilidade, defaults e AUTO_INCREMENT conforme o Draw.io.
16. espaco: chave primaria conforme o Draw.io.
17. inscricoes_atividade: colunas, tipos, nulabilidade, defaults e AUTO_INCREMENT conforme o Draw.io.
18. inscricoes_atividade: chave primaria conforme o Draw.io.
19. credencial: colunas, tipos, nulabilidade, defaults e AUTO_INCREMENT conforme o Draw.io.
20. credencial: chave primaria conforme o Draw.io.
21. Restricoes UNIQUE correspondem ao diagrama.
22. Todas as FKs preservam os vinculos e as acoes referenciais anteriores.
23. Q1: resultado integral da consulta JOIN conferido.
24. Q2: resultado integral da consulta JOIN conferido.
25. Q3: resultado integral da consulta JOIN conferido.
26. Q4: resultado integral da consulta JOIN conferido.
27. Q5: resultado integral da consulta JOIN conferido.
28. Q6: resultado integral da consulta JOIN conferido.
29. Pessoa pode existir sem pertencer a uma subclasse.
30. Palestrante pode ministrar mais de uma atividade.
31. Trigger preenche data de inscricao ausente.
32. Trigger preserva data de inscricao informada.
33. DML corrige telefone e cancela apenas a inscricao demonstrada.
34. Heranca permite sobreposicao de subclasses.
35. Heranca rejeita subclasse sem pessoa.
36. N:M rejeita inscricao duplicada.
37. 1:1 rejeita segunda credencial do mesmo participante.
38. Credencial exige participante nao nulo.
39. Credencial rejeita participante inexistente.
40. UNIQUE rejeita email duplicado.
41. Autorrelacionamento rejeita pre-requisito inexistente.
42. Procedure informa ausencia sem criar inscricao.
43. Procedure permite repetir check-in ja confirmado.
44. Function calcula percentual e trata denominador zero.
45. View e function mantem atividades vazias e calculam percentuais.
46. Relatorio reflete novas inscricoes e check-ins.
47. Check-in NULL nao e contado como presenca.
48. DELETE CASCADE remove dependencias da pessoa.
49. DELETE SET NULL preserva atividade sem espaco.
50. DELETE SET NULL preserva atividade sem palestrante.
51. Exclusao do pre-requisito preserva as atividades dependentes.
52. recepcao_ana: ROLE ativa por padrao.
53. recepcao_ana: consulta view e function e executa procedure.
54. recepcao_ana: UPDATE permitido na coluna check-in.
55. recepcao_ana: DELETE negado.
56. recepcao_ana: UPDATE em outra coluna negado.
57. recepcao_ana: INSERT negado.
58. recepcao_bruno: ROLE ativa por padrao.
59. recepcao_bruno: consulta view e function e executa procedure.
60. recepcao_bruno: UPDATE permitido na coluna check-in.
61. recepcao_bruno: DELETE negado.
62. recepcao_bruno: UPDATE em outra coluna negado.
63. recepcao_bruno: INSERT negado.
64. Uma procedure, uma function, uma view e um trigger.
65. Arquivo Draw.io preservado durante a validacao.

## Evidências e limites

A saída completa das consultas do script principal está em `validacao/saida_script_principal.txt`. Os cenários de mutação adicionais usam ROLLBACK quando necessário, preservando os resultados demonstrados no script.

O confronto automático com o Draw.io verifica as sete tabelas, nomes e ordem das colunas, tipos, nulabilidade, defaults, AUTO_INCREMENT, PKs, UNIQUEs e vínculos de FKs. BOOLEAN é comparado com sua representação tinyint(1) no MySQL. As ações referenciais foram conferidas com o SQL anterior e com os comportamentos de CASCADE e SET NULL.

As consultas Q1 a Q6 são extraídas do próprio script entregue e seus resultados completos são comparados com os resultados esperados da carga fictícia. Os dois diagramas foram comparados por entidades, atributos, cardinalidades e vínculos. Três notas explicativas presentes apenas no arquivo anterior foram identificadas e desconsideradas nessa comparação estrutural; os arquivos e sua disposição visual não precisam ser idênticos.

Isso comprova execução local dos scripts e dos casos listados. Não comprova execução na conexão habitual do estudante, configuração de outro servidor, testes de carga ou aceitação pelo professor.

SHA-256 do Draw.io preservado: `3fd96d53d632a5064721597ae663a7ea9e51f224cd88343a1ac2e0908008c388`.
