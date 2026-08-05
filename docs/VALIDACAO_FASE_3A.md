# Validação da Fase 3A — contratos e arquitetura

Data da validação: 5 de agosto de 2026.

## Escopo concluído

O incremento 3A estabelece a base para documentos narrativos sem antecipar a
extração de conteúdo:

- envelope comum versionado, com identificador determinístico e proteção contra
  inclusão acidental do caminho absoluto da fonte;
- contrato `text_document` para TXT e Markdown;
- contrato `pdf_document` com referências explícitas a páginas;
- contrato `word_document` com blocos na ordem original;
- um JSON Schema Draft 2020-12 independente para cada contrato;
- interface incremental comum para novos conversores;
- registro de conversores por extensão, com detecção de conflitos;
- dependências narrativas declaradas e verificadas no ambiente do projeto.

Os contratos permanecem na versão `1.0`, assim como `email_message`. Todos usam
os campos comuns `schema_version`, `record_type`, `record_id`, `source`, `data` e
`processing`. O campo `source.file_name` aceita somente o nome do arquivo; o
caminho absoluto continua restrito ao relatório local da conversão.

## Estrutura dos contratos

### `text_document`

Registra o conteúdo limpo, a codificação detectada, o formato do conteúdo,
título principal, títulos com número de linha e seções detectadas com seus
intervalos de linhas. O mesmo contrato atende a TXT e Markdown, preservando a
distinção em `source.file_type` e `data.content_format`.

### `pdf_document`

Registra título, autor, quantidade de páginas e uma unidade por página com
`page_number`, `text` e `extraction_method`. Também cataloga sumário hierárquico,
arquivos incorporados e imagens. O indicador `processing.ocr_applied` já faz
parte do contrato, embora OCR não integre este incremento.

### `word_document`

Preserva a ordem lógica por meio de blocos tipados: título, parágrafo, item de
lista e tabela. As seções apontam para intervalos inclusivos desses blocos, sem
duplicar conteúdo.

## Interface extensível

`RecordConverter` define conversores que recebem um `ConversionContext` comum e
produzem registros por iterador. Esse modelo favorece processamento incremental
e mantém disponíveis o cancelamento, o progresso, a data da conversão e opções
específicas.

`ConverterRegistry` associa extensões normalizadas aos conversores. O registro é
atômico: identificadores duplicados ou extensões ambíguas são recusados antes de
alterar o estado. Assim, um adaptador avançado futuro, inclusive com Docling,
poderá ser acrescentado sem mudar os contratos nem o orquestrador.

## Dependências verificadas

O ambiente Python 3.14.6 instalou e importou corretamente:

- `charset-normalizer` 3.4.9;
- `markdown-it-py` 4.2.0;
- `pypdf` 6.14.2;
- `python-docx` 1.2.0;
- `lxml` 6.1.1, dependência binária de `python-docx`.

Os limites de versão declarados no projeto permitem atualizações compatíveis
dentro da versão principal adotada.

## Validação automatizada

A suíte passou com 33 testes. Além das regressões das fases anteriores, ela
valida:

- os três JSON Schemas e registros artificiais representativos;
- estabilidade dos identificadores de registros textuais;
- referências de página e catálogos de PDF;
- ordem de blocos e seções de DOCX;
- proibição de caminhos no envelope de documentos;
- resolução por extensão, conflitos e erros do registro de conversores;
- disponibilidade da pilha narrativa aprovada.

Também passaram análise estática, verificação de formatação e compilação dos
módulos.

## Fora do escopo deste incremento

O 3A não converte arquivos TXT, Markdown, PDF ou DOCX e não altera a seleção de
arquivos da CLI ou da interface desktop. A implementação dos adaptadores reais,
suas fixtures e a integração ao fluxo de saída pertencem aos próximos
incrementos da Fase 3.
