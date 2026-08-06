# Validação da Fase 3D — DOCX

Data da validação: 6 de agosto de 2026.

## Escopo concluído

O incremento 3D encerra a Fase 3 — Documentos narrativos com a conversão local
de DOCX para Markdown:

- seleção pela CLI e pela interface desktop;
- despacho pelo registro comum de conversores;
- validação prévia da estrutura ZIP/OOXML e limites de descompactação;
- leitura ordenada de títulos, parágrafos, listas e tabelas;
- identificação de listas numeradas, marcadores e níveis;
- construção de seções a partir da hierarquia dos títulos;
- título e autor obtidos das propriedades do documento;
- construção e validação do contrato `word_document@1.0`;
- Markdown com referências explícitas aos intervalos de blocos;
- particionamento simultâneo por bytes e tokens estimados;
- progresso, cancelamento, relatório e LEIA-ME específicos para DOCX.

## Ordem estrutural e saída

O conversor usa a ordem real dos elementos no corpo do documento. Parágrafos e
tabelas não são lidos em coleções separadas, evitando que uma tabela seja
deslocada para o fim da saída.

Cada parte Markdown começa com metadados locais e utiliza os marcadores:

```text
<!-- LIMEBH_WORD_BLOCK_START start=N end=M -->
<!-- LIMEBH_WORD_BLOCK_END start=N end=M -->
```

Títulos usam níveis Markdown de 1 a 6. Listas consecutivas permanecem agrupadas
e itens aninhados recebem indentação. Tabelas simples viram tabelas Markdown;
caracteres `|` dentro de células são escapados e quebras internas viram `<br>`.

Quando uma tabela precisa ser particionada, o cabeçalho é repetido em cada
segmento. Unidades textuais grandes preferem limites de parágrafo, linha e
palavra antes do corte estrito.

## Robustez para DOCX gerado por terceiros

O teste com um documento real gerado por `html-to-docx` motivou um incremento
de robustez. Alguns geradores gravam todos os parágrafos como estilo `Normal`,
mesmo quando o texto está visualmente em negrito e funciona como título. Nesses
casos, o conversor pode inferir conservadoramente:

- um título curto em negrito com tamanho explícito de pelo menos 14 pontos;
- títulos numerados curtos cujo conteúdo inteiro esteja em negrito;
- a primeira linha de uma tabela como cabeçalho quando ela é curta, completa e
  possui indicação visual ou é seguida por células claramente descritivas.

As inferências aparecem no contrato, no relatório e no LEIA-ME. Estilos Word
semânticos continuam tendo prioridade, listas reais não são convertidas em
títulos e uma tabela com cabeçalho declarado não é contabilizada como inferida.

O conversor também procura sequências Unicode improváveis associadas a texto
corrompido. Quando encontra alguma, preserva o conteúdo exatamente como está,
marca o resultado como concluído com avisos e informa a quantidade no Markdown,
no relatório e no LEIA-ME. Nenhuma reconstrução automática é aplicada, pois ela
poderia trocar silenciosamente o conteúdo original.

## Segurança e conteúdo omitido

Antes da abertura, o pacote DOCX é verificado quanto à estrutura obrigatória,
tamanho total descompactado, tamanho individual das partes e taxa de compressão
suspeita. A fonte permanece intacta e referências externas não são baixadas.

O relatório contabiliza imagens, cabeçalhos e rodapés omitidos. Também registra
quando detecta comentários, notas, alterações controladas, caixas de texto,
equações, gráficos, diagramas, objetos incorporados, macros ou tabelas aninhadas.
O conteúdo interno desses recursos avançados não entra no Markdown deste
incremento.

## Fixture artificial

A fixture `tests/fixtures/artificial_document.docx` é determinística e contém:

- duas páginas separadas por quebra explícita;
- propriedades de título e autor;
- cinco seções com dois níveis de títulos;
- parágrafos em português;
- listas com marcadores, numeração e item aninhado;
- tabela simples com cabeçalho e três colunas;
- uma imagem raster;
- cabeçalho e rodapé artificiais.

Ela usa o preset `standard_business_brief`: página Letter, margens de 1
polegada, Calibri 11, hierarquia de títulos azul, espaçamento controlado,
numeração Word real e tabela de 9360 DXA com colunas e margens explícitas.

## Validação automatizada

A suíte cobre:

- conformidade com o JSON Schema e preservação do hash da fonte;
- ordem dos blocos e intervalos das seções;
- lista aninhada e distinção entre marcador e numeração;
- tabela com cabeçalho, células e escape de `|`;
- metadados e recursos omitidos;
- detecção de caracteres suspeitos sem alteração do texto;
- inferência conservadora de títulos e cabeçalhos de tabela;
- segmentação de parágrafo grande dentro dos limites;
- DOCX inválido sem exposição do conteúdo;
- cancelamento seguro;
- integração completa pela CLI e pelo worker desktop;
- geometria, estilos, listas e tabela da fixture;
- regressão dos fluxos MBOX, TXT, Markdown e PDF.

## Validação visual

O renderizador canônico `render_docx.py` foi executado, mas o ambiente não
possui LibreOffice (`soffice`) nem Microsoft Word. Conforme o procedimento de
documentos, a inspeção visual por PNG não pôde ser concluída neste ambiente. A
fixture passou pela auditoria estrutural de estilos e geometria; a renderização
visual deverá ser confirmada manualmente ao abrir a fixture no Word ou em outra
suíte compatível.

## Fora do escopo

DOC, DOCM, reconstrução visual avançada, conteúdo de imagens, cabeçalhos,
rodapés, comentários, notas, alterações controladas, caixas de texto, equações,
SmartArt, gráficos, objetos incorporados, macros e tabelas aninhadas permanecem
fora do 3D. Esses elementos são detectados de forma conservadora quando
possível e aparecem no relatório como conteúdo omitido.
