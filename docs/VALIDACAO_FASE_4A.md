# Validação da Fase 4A — contratos e arquitetura tabular

Data da validação: 6 de agosto de 2026.

## Escopo concluído

O incremento 4A estabelece a base para dados tabulares sem antecipar os
conversores de CSV e XLSX:

- contrato `tabular_dataset` para CSV;
- contrato `spreadsheet_workbook` para abas, intervalos e tabelas de XLSX;
- JSON Schema Draft 2020-12 independente para cada contrato;
- representação compacta de linhas, acompanhada de colunas tipadas;
- segmentação explícita por intervalo de linhas;
- política segura e auditável para fórmulas de planilha;
- dependência XLSX declarada e verificada no ambiente do projeto.

Os contratos usam o envelope comum `1.0`. O caminho absoluto da fonte continua
restrito ao relatório local; os registros recebem somente o nome do arquivo.

## Modelo de dados

As colunas têm índice, nome normalizado, nome original, tipo inferido e indicador
de nulabilidade. Os tipos previstos são vazio, booleano, inteiro, número, data,
data e hora, hora, texto e misto. Cada segmento registra o total de linhas do
conjunto e o intervalo incluído, permitindo que arquivos grandes sejam emitidos
incrementalmente sem mudar o contrato.

O CSV também registra codificação, delimitador, aspas, escape e terminador de
linha. Linhas irregulares, linhas vazias ignoradas, cabeçalho inferido e tamanho
da amostra de inferência ficam auditáveis em `processing`.

O XLSX preserva o contexto da pasta de trabalho, da aba e do intervalo ou tabela.
As linhas recebem os valores armazenados no arquivo. Quando houver fórmula, o
valor em cache pode ser usado na linha e a expressão original é preservada em
metadados. Fórmulas não são executadas e vínculos externos não são seguidos.

## Dependência aprovada

CSV será lido com a biblioteca padrão `csv`. Para XLSX foi adotado
`openpyxl>=3.1,<4`, que oferece leitura em modo somente leitura e acesso separado
a fórmulas e valores em cache. O conversor será responsável por fechar cada
pasta de trabalho explicitamente.

## Validação automatizada

Os testes artificiais cobrem a validade dos schemas, identificadores estáveis,
tipos escalares e temporais, contexto de abas e intervalos, metadados de fórmula
e rejeição de colunas ambíguas, linhas irregulares e números não finitos.
A suíte completa passou com 82 testes, além da análise estática, verificação de
formatação e compilação dos módulos.

## Fora do escopo deste incremento

O 4A não lê arquivos CSV ou XLSX, não cria fixtures e não altera CLI, interface
desktop ou geração de saída. A conversão real e suas integrações pertencem aos
incrementos 4B e 4C.
