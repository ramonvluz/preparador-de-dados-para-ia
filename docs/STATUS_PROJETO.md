# Status do projeto

**Atualizado em:** 19 de agosto de 2026  
**Versão do aplicativo:** 0.1.0  
**Situação:** Fases 1 a 4 concluídas; Fase 5 ainda não iniciada

## Entregas concluídas

| Fase | Entrega | Status |
|---|---|---|
| 1 | Núcleo modular, contrato de e-mail, MBOX, CLI e saída auditável | Concluída |
| 2 | Interface desktop, Downloads, progresso, cancelamento e resultados | Concluída |
| 3 | TXT, Markdown, PDF e DOCX | Concluída |
| 4 | Contratos tabulares, CSV e XLSX | Concluída |
| 5 | Detecção e anonimização opcional de dados pessoais | Próxima |
| 6 | Empacotamento, identidade visual e distribuição Windows | Planejada |

## Validações atuais

- MBOX real de aproximadamente 2,66 GiB: 3.699 mensagens convertidas sem falha.
- CSV real: 113.036 linhas, 18 colunas e 19 partes, sem perdas ou falhas.
- XLSX real: contrato `spreadsheet_workbook@1.0`, aba, intervalo, cabeçalhos,
  tipos e datas preservados, sem falhas.
- Suíte automatizada: 101 testes aprovados.
- Qualidade: análise estática e compilação aprovadas.

## Capacidades disponíveis

- Fontes: MBOX, TXT, Markdown, PDF, DOCX, CSV e XLSX.
- Saídas estruturadas: JSON e JSONL particionados.
- Saídas narrativas: Markdown particionado.
- Processamento local, original intocado, relatório e `LEIA-ME.txt`.
- Interface gráfica e CLI.

## Limites conhecidos

- Uma fonte por conversão na interface.
- Sem detecção ou anonimização de dados pessoais nesta versão.
- XLSX sem suporte a `.xls`; fórmulas não são executadas.
- Células fora de tabelas do Excel não são incluídas quando a aba contém tabelas.
- Planilhas XLSX muito grandes ainda exigem teste específico de memória.
- Refinamento visual e empacotamento Windows pertencem à Fase 6.

## Evoluções futuras adiadas

- `body_analysis` conservador para e-mails.
- Extração do conteúdo de anexos.
- OCR de imagens e PDFs digitalizados.

Esses itens não fazem parte da Fase 5 nem do escopo imediato do produto.

## Próximo passo recomendado

Planejar a Fase 5 antes de implementar. O primeiro incremento recomendado é a
detecção local e auditável de possíveis dados pessoais, apenas para contagem e
aviso no relatório, sem anonimização automática nesta primeira entrega.
