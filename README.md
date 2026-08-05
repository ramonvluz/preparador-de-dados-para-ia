# Preparador de Dados para IA da LIMEBH

Aplicação local para converter, limpar, estruturar e particionar arquivos
administrativos antes do uso em plataformas de IA ou integrações via API.

Este repositório contém a nova base modular do produto. A base atual implementa
a conversão incremental de MBOX, o contrato versionado
`email_message`, limpeza Unicode auditável, particionamento por bytes e tokens,
saídas JSON/JSONL, relatório, cancelamento seguro, CLI e interface desktop.

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
pasta exclusiva para a conversão. O perfil `platform` gera JSON particionado e
o perfil `api` gera JSONL particionado.

```powershell
.\.venv\Scripts\limebh-preparador.exe emails.mbox --profile api
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

A interface seleciona um MBOX, recomenda JSON ou JSONL conforme o perfil,
utiliza `Downloads\Preparador LIMEBH` por padrão e executa a conversão em uma
thread separada. O cancelamento preserva partes concluídas e válidas.

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
