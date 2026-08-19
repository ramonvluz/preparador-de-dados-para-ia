# Validação de equivalência do primeiro incremento

## Baseline validado no protótipo

O relatório local de referência foi lido apenas para métricas, sem copiar MBOX
ou saídas reais para este projeto:

| Métrica | Resultado conhecido |
|---|---:|
| Mensagens encontradas | 3.699 |
| Mensagens convertidas | 3.699 |
| Falhas | 0 |
| Partes | 17 |
| Maior parte | 999.425 bytes |
| Alterações Unicode | 7.690 |
| Contrato | `email_message@1.0` |

O baseline também confirma labels e threads do Gmail, relações de resposta,
catálogo de anexos sem binários, JSON particionado e a estrutura
`PRONTO_PARA_IA`/`LEIA-ME.txt`/relatório.

## Equivalência verificada no projeto novo

Os testes automatizados exercitam os mesmos comportamentos com uma fixture MBOX
integralmente artificial:

- leitura incremental pela biblioteca `mailbox`, sem carregar o MBOX completo;
- contrato `email_message@1.0` validado pelo JSON Schema migrado;
- preservação de labels, thread, `In-Reply-To` e `References`;
- catálogo de anexos com `content_extracted: false`, sem Base64 na saída;
- limpeza Unicode auditável, preservando acentos, emojis e pontuação;
- divisão simultânea por bytes e tokens, inclusive mensagem superdimensionada;
- JSON para plataforma e JSONL particionado para API;
- fonte inalterada e caminho absoluto ausente dos arquivos destinados à IA;
- recusa de sobrescrita e escrita atômica;
- cancelamento com partes e relatório válidos;
- CLI chamando o caso de uso do núcleo.

## Regressão com a fonte real

Em 5 de agosto de 2026, a nova CLI processou a fonte real diretamente no local
original, sem movê-la ou copiá-la. A saída foi criada pelo comportamento padrão
do produto em `Downloads\Preparador de Dados para IA`, fora do repositório.

| Verificação | Resultado da nova base |
|---|---:|
| Mensagens encontradas | 3.699 |
| Mensagens convertidas | 3.699 |
| Falhas | 0 |
| Partes JSON | 17 |
| Maior parte | 999.755 bytes |
| Maior estimativa por parte | 499.878 tokens |
| Alterações Unicode | 7.690 |
| Anexos catalogados | 2.699 |
| Duração | 323,93 segundos |

Os 3.699 registros foram validados individualmente pelo JSON Schema, sem erro.
Também foram verificados:

- 3.699 `record_id` distintos;
- 3.699 registros com `thread_id` e labels do Gmail;
- 1.439 registros com `In-Reply-To`;
- 1.522 registros com `References`;
- nenhum binário de anexo incorporado;
- nenhum caminho absoluto nos arquivos destinados à IA;
- nenhuma parte temporária ou incompleta;
- tamanho e data de modificação da fonte inalterados após a conversão.

A diferença de 330 bytes entre a maior parte antiga e a nova não altera a
equivalência funcional: ambas permanecem abaixo dos limites configurados, e a
nova base reproduziu exatamente as contagens de mensagens, partes, anexos e
normalizações Unicode do baseline.
