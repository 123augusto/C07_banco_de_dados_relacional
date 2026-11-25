**Banco de Dados: Festival de Inovação do Inatel**

**Integrantes do Grupo:** Augusto Leite e Vitor Augusto.

**Sobre o Projeto:** Neste projeto, criamos um banco de dados para organizar o Festival de Inovação do Inatel, um evento de dois dias com palestras, oficinas e mesas-redondas para alunos e a comunidade externa.

Usamos o MySQL 8 para cadastrar participantes, palestrantes, espaços, atividades, inscrições e credenciais. Implementamos a herança entre Pessoa, Participante e Palestrante e registramos os pré-requisitos entre as atividades.

Na segunda entrega, adicionamos uma Procedure para registrar o check-in, uma View para consultar o resumo das atividades, um Trigger para preencher a data da inscrição quando ela não é informada e uma Function para calcular o percentual de presença.

Também criamos dois usuários com uma ROLE em comum para definir suas permissões de acesso. Fizemos consultas com JOIN usando os relacionamentos 1:1, 1:N e N:M para buscar informações sobre participantes, credenciais, espaços e atividades.

Para demonstrar o funcionamento do banco, inserimos pelo menos cinco registros fictícios em cada tabela e usamos comandos de inserção, atualização e exclusão. As funcionalidades e os motivos de cada implementação estão descritos na documentação do projeto.

[Documentação da etapa](DOCUMENTACAO.md) · [Diagrama](segundaEntrega.drawio) · [Script SQL](segundaEntrega.sql) · [Usuários e ROLE](usuarios_roles.sql)
