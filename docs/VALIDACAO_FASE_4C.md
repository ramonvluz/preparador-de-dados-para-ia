# Validação da Fase 4C — XLSX

## Escopo

O incremento 4C adiciona conversão local de arquivos `.xlsx` para o contrato
versionado `spreadsheet_workbook`, com saída JSON no perfil `platform` e JSONL
no perfil `api`.

## Comportamento implementado

- identifica abas visíveis, ocultas e muito ocultas;
- converte tabelas do Excel ou, na ausência delas, o intervalo utilizado da aba;
- preserva nomes e referências de abas, tabelas e intervalos;
- normaliza cabeçalhos e infere tipos sem transformar códigos textuais em números;
- cataloga fórmulas e utiliza somente valores em cache quando disponíveis;
- nunca executa fórmulas nem segue vínculos externos;
- registra mesclagens e linhas ou colunas ocultas no relatório;
- segmenta conjuntos grandes sem perder o intervalo lógico das linhas;
- valida a estrutura ZIP do XLSX e limita conteúdo descompactado suspeito;
- mantém o arquivo original inalterado.

## Verificação automatizada

Os testes cobrem contrato JSON Schema, tabelas, intervalos, fórmulas sem cache,
abas ocultas, células mescladas, segmentação, pacote inválido, perfis JSON/JSONL,
CLI e execução pela interface desktop.

Execute a validação completa com:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1
```

## Limites conscientes

- arquivos `.xls` legados não são aceitos;
- fórmulas não são recalculadas;
- recursos visuais, macros e objetos incorporados não são convertidos;
- quando uma aba possui tabelas do Excel, cada tabela é tratada como conjunto de
  dados; células externas às tabelas não integram esses conjuntos nesta fase.
