# Preparador de Dados para IA da LIMEBH

Aplicação local para converter, limpar, estruturar e particionar arquivos
administrativos antes do uso em plataformas de IA ou integrações via API.

Este repositório contém a nova base modular do produto. A base atual implementa
a conversão incremental de MBOX, o contrato versionado `email_message`, limpeza
Unicode auditável, particionamento por bytes e tokens, saídas JSON/JSONL,
relatório, cancelamento seguro, CLI e interface desktop.

A Fase 3 converte TXT, Markdown, PDF e DOCX para partes Markdown
autossuficientes. PDFs preservam referências explícitas de página e catalogam
sumário, anexos e imagens sem copiar seus binários. DOCX preserva a ordem de
títulos, parágrafos, listas, seções e tabelas simples, registrando os recursos
avançados que não entram na saída. Quando faltam estilos semânticos, o conversor
infere de forma conservadora títulos em negrito e cabeçalhos prováveis de tabela.
Sequências de caracteres suspeitas geram aviso, mas nunca são corrigidas
automaticamente.

A Fase 4 implementa contratos e conversores para CSV e XLSX, com colunas tipadas,
segmentos de linhas, contexto de abas e intervalos e preservação auditável de
fórmulas. CSV detecta codificação, delimitador, cabeçalho e tipos. XLSX preserva
abas, tabelas do Excel, intervalos, visibilidade e fórmulas sem executá-las nem
seguir vínculos externos. Os arquivos originais não são alterados.

## Princípios de segurança

- O processamento é local e não envia dados para a internet.
- A fonte é lida no local original e não é alterada, movida ou copiada.
- Anexos são apenas catalogados; seus binários não entram nos JSONs.
- O caminho absoluto da fonte aparece somente no relatório local.
- Erros por mensagem não registram o conteúdo da mensagem.

## Preparação do ambiente

No PowerShell, a partir da raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Uso da CLI

```powershell
.\.venv\Scripts\limebh-preparador.exe "C:\caminho\emails.mbox"
```

Por padrão, o resultado é criado em `Downloads\Preparador LIMEBH`, com uma
pasta exclusiva para a conversão. Para MBOX, o perfil `platform` gera JSON
particionado e o perfil `api` gera JSONL. TXT e Markdown geram Markdown
particionado nos dois perfis. PDF gera Markdown com marcadores explícitos de
página e DOCX gera Markdown estruturado, conforme a recomendação automática do
PRD. CSV e XLSX geram JSON tabular no perfil `platform` e JSONL no perfil `api`.

```powershell
.\.venv\Scripts\limebh-preparador.exe emails.mbox --profile api
.\.venv\Scripts\limebh-preparador.exe manual.txt
.\.venv\Scripts\limebh-preparador.exe orientacoes.md --profile api
.\.venv\Scripts\limebh-preparador.exe relatorio.pdf
.\.venv\Scripts\limebh-preparador.exe manual.docx
.\.venv\Scripts\limebh-preparador.exe dados.csv --profile api
.\.venv\Scripts\limebh-preparador.exe planejamento.xlsx
.\.venv\Scripts\limebh-preparador.exe emails.mbox --output C:\saida\conversao
.\.venv\Scripts\limebh-preparador.exe emails.mbox --max-size-mb 25 --max-tokens 250000
```

Use `--help` para consultar todas as opções. Limites são configuráveis e não
representam garantias permanentes de plataformas externas.

## Interface desktop

Inicie a aplicação gráfica pelo executável instalado no ambiente virtual:

```powershell
.\.venv\Scripts\limebh-preparador-gui.exe
```

Também é possível executar diretamente como módulo:

```powershell
.\.venv\Scripts\python.exe -m limebh_preparador.ui
```

A interface seleciona MBOX, TXT, Markdown, PDF, DOCX, CSV ou XLSX e apresenta a saída
recomendada para cada combinação de fonte e perfil. Ela utiliza `Downloads\Preparador
LIMEBH` por padrão e executa a conversão em uma thread separada. O cancelamento
preserva partes concluídas e válidas.

## Verificação

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1
```

O script executa os testes, a análise estática e a compilação dos módulos. As
fixtures em `tests/fixtures` são artificiais e usam domínios reservados.

## Documentação

- [PRD](docs/PRD.md)
- [Validação de equivalência](docs/VALIDACAO_EQUIVALENCIA.md)
- [Validação da Fase 2 — MVP desktop](docs/VALIDACAO_FASE_2.md)
- [Validação da Fase 3A — contratos e arquitetura](docs/VALIDACAO_FASE_3A.md)
- [Validação da Fase 3B — TXT e Markdown](docs/VALIDACAO_FASE_3B.md)
- [Validação da Fase 3C — PDF](docs/VALIDACAO_FASE_3C.md)
- [Validação da Fase 3D — DOCX](docs/VALIDACAO_FASE_3D.md)
- [Validação da Fase 4A — contratos e arquitetura tabular](docs/VALIDACAO_FASE_4A.md)
- [Validação da Fase 4B — CSV](docs/VALIDACAO_FASE_4B.md)
- [Validação da Fase 4C — XLSX](docs/VALIDACAO_FASE_4C.md)
