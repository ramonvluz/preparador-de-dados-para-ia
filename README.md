# Preparador de Dados para IA da LIMEBH

Aplicação local para converter, limpar, estruturar e particionar arquivos
administrativos antes do uso em plataformas de IA ou integrações via API.

Este repositório contém a nova base modular do produto. A base atual implementa
a conversão incremental de MBOX, o contrato versionado `email_message`, limpeza
Unicode auditável, particionamento por bytes e tokens, saídas JSON/JSONL,
relatório, cancelamento seguro, CLI e interface desktop.

A Fase 3 já converte TXT e Markdown para partes Markdown autossuficientes, com
detecção de codificação, títulos, seções e limpeza Unicode auditável. Os
contratos de PDF e DOCX, a interface comum de conversores e o registro extensível
por extensão também estão prontos para os próximos incrementos.

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
particionado nos dois perfis, conforme a recomendação automática do PRD.

```powershell
.\.venv\Scripts\limebh-preparador.exe emails.mbox --profile api
.\.venv\Scripts\limebh-preparador.exe manual.txt
.\.venv\Scripts\limebh-preparador.exe orientacoes.md --profile api
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

A interface seleciona MBOX, TXT ou Markdown e apresenta a saída recomendada
para cada combinação de fonte e perfil. Ela utiliza `Downloads\Preparador
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
