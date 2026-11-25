# Validação da primeira entrega

O [resultado original](resultado_mysql_original.json) registra as verificações do SQL e do modelo relacional. Os arquivos em [`fontes`](../fontes) são as versões usadas como entrada na revisão da modelagem.

## Gerar o modelo revisado

Instale Pillow e execute o gerador a partir da raiz do repositório. O script grava em `entrega_01/validacao/gerados` o diagrama, as prévias, o SQL e as somas de verificação das fontes.

```bash
python -m pip install Pillow
python entrega_01/validacao/gerar_revisao_projeto.py
```

## Validar o SQL

Use uma instância MySQL isolada e vazia. Defina `C07_MYSQL_TEST_DATADIR` com o diretório de dados da instância. O script conecta como `root` a `127.0.0.1` e usa a porta `33079` por padrão. Defina `C07_MYSQL_TEST_PORT` para usar outra porta ou `C07_MYSQL_CLIENT` para indicar outro executável `mysql`.

```bash
python entrega_01/validacao/validar_projeto_mysql.py
```

O script confere o diretório de dados antes de criar `festival_inovacao`, executa as verificações e grava `validacao_mysql.json` em `entrega_01/validacao/gerados`.
