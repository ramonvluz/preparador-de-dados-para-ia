# Status do projeto

**Atualizado em:** 5 de outubro de 2026
**Versão do aplicativo:** 0.1.0
**Situação:** MVP 0.1.0 concluído e validado no Windows

## Entregas concluídas

| Fase | Entrega | Status |
|---|---|---|
| 1 | Núcleo modular, contrato de e-mail, MBOX, CLI e saída auditável | Concluída |
| 2 | Interface desktop, Downloads, progresso, cancelamento e resultados | Concluída |
| 3 | TXT, Markdown, PDF e DOCX | Concluída |
| 4 | Contratos tabulares, CSV e XLSX | Concluída |
| 5 | Privacidade e conteúdo avançado | Adiada |
| 6 | Empacotamento, identidade visual e distribuição Windows | Concluída |

## Validações atuais

- MBOX real de aproximadamente 2,66 GiB: 3.699 mensagens convertidas sem falha.
- CSV real: 113.036 linhas, 18 colunas e 19 partes, sem perdas ou falhas.
- XLSX real: contrato `spreadsheet_workbook@1.0`, aba, intervalo, cabeçalhos,
  tipos e datas preservados, sem falhas.
- Suíte automatizada: 105 testes aprovados.
- Qualidade: análise estática e compilação aprovadas.
- Build portátil `onedir` iniciado com sucesso sem usar o Python do ambiente virtual.
- ZIP portátil descompactado e iniciado com título, ícone, versão e manual corretos.
- Versão portátil testada com sucesso em outro computador Windows.

## Capacidades disponíveis

- Fontes: MBOX, TXT, Markdown, PDF, DOCX, CSV e XLSX.
- Saídas estruturadas: JSON e JSONL particionados.
- Saídas narrativas: Markdown particionado.
- Processamento local, original intocado, relatório e `LEIA-ME.txt`.
- Interface gráfica e CLI.
- Camada compacta em `PRONTO_PARA_IA`, com auditoria técnica separada no relatório.

## Limites conhecidos

- Uma fonte por conversão na interface.
- Sem detecção ou anonimização de dados pessoais nesta versão; recurso adiado.
- XLSX sem suporte a `.xls`; fórmulas não são executadas.
- Células fora de tabelas do Excel não são incluídas quando a aba contém tabelas.
- Planilhas XLSX muito grandes ainda exigem teste específico de memória.
- Refinamento visual adicional e instalador pertencem à continuação da Fase 6.

## Evoluções futuras adiadas

- `body_analysis` conservador para e-mails.
- Extração do conteúdo de anexos.
- OCR de imagens e PDFs digitalizados.
- Detecção e anonimização opcional de dados pessoais.

Esses itens não fazem parte do MVP nem do escopo imediato do produto.

## Próximo passo recomendado

Publicar o código-fonte como projeto de portfólio e registrar a versão `v0.1.0`.
O instalador, o refinamento visual adicional e os recursos avançados permanecem
como evoluções futuras opcionais.
