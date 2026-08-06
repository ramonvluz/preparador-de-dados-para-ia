# Validação da Fase 3C — PDF

Data da validação: 6 de agosto de 2026.

## Escopo concluído

O incremento 3C implementa a conversão local de PDF para Markdown:

- seleção pela CLI e pela interface desktop;
- despacho pelo registro comum da Fase 3A;
- leitura do texto incorporado página a página com `pypdf`;
- construção e validação do contrato `pdf_document@1.0`;
- metadados de título e autor;
- sumário hierárquico com referências de página;
- catálogo de anexos e imagens, sem copiar os binários;
- Markdown com marcadores explícitos de início e fim de cada página;
- particionamento por bytes e tokens sem perder o vínculo com a página;
- progresso, cancelamento, relatório e LEIA-ME específicos para PDF.

## Extração e representação

Cada página registra número, texto e método de extração. Neste incremento os
métodos produzidos são `embedded_text` ou `none`; `ocr` permanece reservado no
contrato para evolução futura. A extração usa o modo de layout do `pypdf` para
obter uma ordem de leitura útil, sem prometer reprodução visual do documento.

Cada parte Markdown começa com metadados locais e utiliza os marcadores:

```text
<!-- LIMEBH_PAGE_START page=N -->
<!-- LIMEBH_PAGE_END page=N -->
```

Quando uma página isolada excede o limite configurado, ela é segmentada e os
marcadores também registram o número e o total do segmento. Páginas vazias
recebem uma nota explícita de que não houve texto incorporado e de que OCR não
foi aplicado.

## Catálogos e limites de segurança

Anexos incorporados registram somente nome, tipo de mídia e tamanho declarado.
Imagens registram página, número, tipo e dimensões. O conteúdo binário desses
itens não é extraído para a saída preparada para IA.

Fluxos de conteúdo codificado acima de 32 MiB por página não são descompactados
para extração textual e geram aviso. PDFs protegidos com senha não são abertos;
o relatório registra somente o tipo da falha. Arquivos que aceitam senha vazia
podem ser lidos e recebem aviso auditável.

## Validação artificial e visual

A fixture `tests/fixtures/artificial_document.pdf` possui três páginas A4:

- duas páginas com texto incorporado;
- uma página composta somente por imagem raster;
- título, autor e sumário hierárquico;
- uma imagem catalogável;
- um anexo de texto artificial.

O arquivo foi renderizado integralmente com Poppler a 144 DPI. As três páginas
foram inspecionadas visualmente e não apresentaram cortes, sobreposições ou
elementos fora da página. A terceira página confirmou visualmente o cenário
sem texto incorporado, e o conversor registrou `page_0003_no_extractable_text`
sem tentar OCR.

## Validação automatizada

A suíte cobre:

- contrato JSON Schema e preservação do hash da fonte;
- texto, metadados, sumário, imagem e anexo;
- página sem texto e ausência deliberada de OCR;
- marcadores explícitos de página;
- segmentação de página grande dentro dos limites;
- relatório de extração e conteúdo omitido;
- PDF protegido por senha sem exposição de conteúdo;
- integração pela CLI, pelo worker desktop e pelo registro de conversores;
- regressão dos fluxos MBOX, TXT e Markdown.

## Fora do escopo

OCR, solicitação interativa de senha, reconstrução visual avançada, extração do
conteúdo binário de imagens ou anexos e conversão de DOCX permanecem fora do
3C. A Fase 3D poderá implementar DOCX com `python-docx`; OCR ou Docling só devem
ser reavaliados quando documentos reais exigirem maior complexidade.
