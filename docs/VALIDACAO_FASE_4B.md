# Validação da Fase 4B — CSV

Data da validação: 19 de agosto de 2026.

## Escopo implementado

O incremento 4B adiciona a conversão real de CSV ao núcleo, à CLI e à interface
desktop. O arquivo original permanece intocado e a saída segue o contrato
`tabular_dataset@1.0` definido no 4A.

O perfil `platform` gera JSON particionado e o perfil `api` gera JSONL. Cada
registro informa as colunas, seus tipos inferidos, o total de linhas e o
intervalo incluído no segmento.

## Leitura e normalização

O conversor usa a biblioteca padrão `csv` e a pilha de detecção de codificação já
adotada pelo projeto. Ele:

- detecta vírgula, ponto e vírgula, tabulação ou barra vertical;
- identifica automaticamente a presença de cabeçalho;
- cria nomes estáveis e exclusivos para colunas;
- preserva identificadores com zeros à esquerda como texto;
- reconhece booleanos, inteiros, números decimais e valores temporais ISO;
- preenche células ausentes em linhas irregulares com `null`;
- ignora linhas completamente vazias e registra a ocorrência no relatório;
- aplica a limpeza Unicode auditável sem corrigir silenciosamente o conteúdo.

As linhas são divididas em segmentos de até mil registros antes da escrita. Um
segmento excepcionalmente grande é mantido e sinalizado no relatório, evitando
perda silenciosa de dados.

## Integração do produto

A CLI e o seletor da interface aceitam `.csv`, exibem progresso em linhas e
recomendam JSON ou JSONL conforme o perfil. O resultado mantém a estrutura já
conhecida do produto: `PRONTO_PARA_IA`, `LEIA-ME.txt` e
`relatorio_conversao.json`.

## Validação automatizada

Os testes artificiais verificam dialeto, cabeçalho, tipos, valores nulos,
acentuação, limpeza de caracteres invisíveis, linhas vazias e irregulares,
segmentação, JSON, JSONL, CLI e recomendações da interface.
A suíte completa passou com 91 testes, além da análise estática, verificação de
formatação e compilação dos módulos.

## Fora do escopo

XLSX permanece reservado ao incremento 4C. A seleção simultânea de vários
arquivos continua registrada para uma fase posterior, conforme decisão anterior
do projeto.
