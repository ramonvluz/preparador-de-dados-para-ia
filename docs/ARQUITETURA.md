# Arquitetura do projeto

## Avaliação

A arquitetura está alinhada às práticas comuns da comunidade Python para uma
aplicação desktop deste porte. O projeto utiliza layout `src`, metadados em
`pyproject.toml`, dependências declaradas, módulos com responsabilidades claras,
JSON Schemas versionados e testes unitários e de integração.

```text
src/preparador_dados_ia/
├── application/   # orquestra os fluxos de conversão
├── contracts/     # contratos e modelos de dados
├── converters/    # leitores específicos por formato
├── core/          # limpeza, cancelamento, caminhos e particionamento
├── outputs/       # escrita atômica e formatos de saída
└── ui/            # interface desktop e worker
```

Na raiz, `schemas`, `tests`, `scripts` e `docs` mantêm artefatos não pertencentes
ao pacote de execução separados do código-fonte.

## Pontos fortes

- conversores independentes e resolvidos por registro;
- núcleo reutilizado pela CLI e pela interface;
- processamento local e preservação dos originais;
- escrita atômica, cancelamento e relatórios auditáveis;
- contratos separados por tipo de documento;
- fixtures artificiais, sem dados reais no repositório;
- cobertura automatizada dos formatos suportados.

## Dívidas aceitáveis no MVP

- a interface está concentrada em um arquivo grande;
- existem fluxos de orquestração distintos para e-mail, documentos e tabelas;
- XLSX usa mais memória que formatos processados por streaming;
- a interface aceita uma fonte por conversão;
- o refinamento visual e a distribuição ainda não foram feitos.

Esses pontos não bloqueiam o MVP e não justificam uma refatoração ampla antes do
empacotamento. Devem ser tratados somente quando uma necessidade real aparecer.

## Regra para o fechamento do MVP

Até a primeira distribuição Windows, serão aceitas apenas correções encontradas
nos testes manuais, ajustes de identidade e mudanças necessárias ao
empacotamento. Recursos novos permanecem fora do escopo.
