# PRD — Preparador de Dados para IA da LIMEBH

## 1. Identificação

- **Produto:** Preparador de Dados para IA da LIMEBH
- **Tipo de documento:** Documento de Requisitos do Produto (PRD)
- **Versão:** 0.2
- **Status:** Fases 1 a 4 concluídas; Fase 5 aguardando planejamento
- **Responsável inicial:** Coordenação de Tecnologia da LIMEBH
- **Plataforma inicial:** Windows desktop

## 2. Visão do produto

O Preparador de Dados para IA da LIMEBH será uma aplicação desktop local que
transforma arquivos administrativos em documentos limpos, estruturados e
particionados para uso em plataformas de inteligência artificial ou integrações
via API.

O produto não será um sistema de armazenamento ou gestão documental. Sua função
é preparar dados existentes para uso por modelos de linguagem, permitindo que
pessoas sem conhecimento técnico executem conversões com segurança e autonomia.

### Proposta de valor

> Selecionar arquivos, preparar o conteúdo para IA e entregar uma pasta pronta
> para uso, sem exigir programação e sem enviar automaticamente os dados para a
> internet.

## 3. Problema

A LIMEBH possui informações importantes distribuídas em e-mails, documentos,
PDFs, planilhas e arquivos de texto. Esses arquivos podem ser grandes, conter
ruído técnico ou usar estruturas pouco adequadas a plataformas de IA.

Atualmente, a preparação exige intervenção de uma pessoa com conhecimento
técnico para:

- identificar o formato;
- extrair o conteúdo relevante;
- preservar metadados úteis;
- limpar problemas de codificação;
- dividir grandes volumes segundo limites de arquivos e tokens;
- explicar o que foi preservado ou descartado;
- organizar os resultados para upload ou uso por API.

## 4. Objetivos

### 4.1 Objetivo principal

Dar autonomia aos integrantes autorizados da LIMEBH para preparar documentos
para análise por LLMs de forma local, simples, rastreável e segura.

### 4.2 Objetivos específicos

- Processar arquivos grandes sem carregá-los integralmente na memória.
- Reconhecer automaticamente os formatos suportados.
- Aplicar um contrato de dados adequado a cada tipo de documento.
- Recomendar JSON, JSONL ou Markdown conforme fonte e destino.
- Dividir as saídas por bytes e estimativa de tokens.
- Informar claramente o que foi extraído, transformado ou omitido.
- Preservar os arquivos originais sem modificá-los ou copiá-los.
- Manter todo o processamento local por padrão.
- Permitir futura distribuição como aplicação Windows portátil ou instalável.

## 5. Não objetivos

A primeira versão não pretende:

- armazenar ou substituir os documentos originais;
- funcionar como sistema de gestão documental;
- enviar arquivos automaticamente a uma plataforma ou API;
- oferecer análise de IA dentro do aplicativo;
- garantir anonimização perfeita de dados pessoais;
- extrair conteúdo de todos os tipos de anexo de e-mail;
- executar OCR de imagens na primeira entrega;
- sincronizar arquivos na nuvem;
- oferecer colaboração multiusuário.

## 6. Usuários

### 6.1 Usuário principal

Integrante da LIMEBH que precisa preparar dados para análise em uma plataforma de
IA, mas não deseja usar scripts ou terminal.

### 6.2 Usuário técnico

Integrante da Coordenação de Tecnologia responsável por validar conversões,
investigar avisos, configurar opções avançadas e evoluir os conversores.

## 7. Princípios do produto

1. **Local por padrão:** nenhum dado será enviado automaticamente à internet.
2. **Original intocado:** a fonte não será alterada, movida ou duplicada.
3. **Saída orientada ao uso:** será gerado apenas o formato necessário ao perfil
   selecionado, sem cópias intermediárias redundantes.
4. **Decisão transparente:** recomendações automáticas serão explicadas e poderão
   ser alteradas pelo usuário.
5. **Contrato por tipo:** cada formato terá uma estrutura apropriada ao seu
   conteúdo, em vez de um JSON genérico forçado.
6. **Rastreabilidade:** toda conversão produzirá um relatório do que ocorreu.
7. **Escalabilidade:** arquivos grandes serão lidos incrementalmente.
8. **Privacidade visível:** o aplicativo alertará quando a saída puder conter
   dados pessoais.

## 8. Jornada principal

1. O usuário abre a aplicação.
2. Seleciona um ou vários arquivos.
3. O aplicativo identifica os formatos.
4. O usuário escolhe o destino de uso:
   - plataforma de IA;
   - API/File Search;
   - personalizado.
5. O aplicativo recomenda o formato de saída e explica a escolha.
6. O usuário confirma ou altera as opções.
7. A conversão é executada em segundo plano.
8. A interface mostra progresso, quantidade processada, avisos e tempo decorrido.
9. O aplicativo apresenta um resumo final.
10. O usuário abre diretamente a pasta `PRONTO_PARA_IA`.

## 9. Interface desktop

### 9.1 Tecnologia inicial

A primeira interface será desktop nativa em Python. Tkinter/ttk será usado no
MVP por fazer parte da biblioteca padrão, oferecer seletor nativo de arquivos e
permitir empacotamento para Windows.

Streamlit não será a interface principal porque arquivos com vários gigabytes
não devem passar por um mecanismo de upload de aplicação web local.

### 9.2 Elementos mínimos

- Seleção de um ou vários arquivos.
- Lista de arquivos e formatos detectados.
- Remoção de itens selecionados.
- Perfil de destino.
- Formato automático ou escolha manual.
- Pasta de destino, com possibilidade de alteração.
- Opções de limpeza e privacidade.
- Botão de início.
- Barra de progresso.
- Contadores de itens processados, avisos e falhas.
- Cancelamento seguro.
- Resumo final.
- Botão `Abrir arquivos prontos para IA`.
- Botão `Abrir relatório`.

### 9.3 Wireframe textual

```text
Preparador de Dados para IA — LIMEBH

Arquivos selecionados
┌──────────────────────────────────────────────────────────────┐
│ emails_bruno.mbox                    MBOX — E-mails          │
│ estatuto.pdf                         PDF — Documento         │
└──────────────────────────────────────────────────────────────┘
[ Adicionar arquivos ] [ Remover ]

Destino de uso:    [ Plataforma de IA ▼ ]
Formato de saída:  [ Automático (recomendado) ▼ ]
Destino local:     [ Downloads\Preparador LIMEBH ] [ Alterar ]

[x] Limpar caracteres invisíveis
[x] Gerar relatório
[ ] Anonimizar dados pessoais

[ Iniciar conversão ]

Progresso: ███████████░░░ 72%
2.681 de 3.699 itens processados
```

## 10. Destino e organização da saída

### 10.1 Destino padrão

A aplicação usará a pasta de Downloads reconhecida pelo sistema operacional.
No Windows, deverá consultar a pasta conhecida do sistema e usar
`~/Downloads` apenas como fallback.

```text
Downloads/
└── Preparador LIMEBH/
```

### 10.2 Pasta por conversão

Cada execução criará uma pasta usando o nome da fonte e o horário local do
início:

```text
emails_bruno__20260805_143025/
```

Em conversões com várias fontes, será usado um nome descritivo como:

```text
conversao_3_arquivos__20260805_143025/
```

Colisões receberão um sufixo incremental, sem sobrescrita:

```text
emails_bruno__20260805_143025__02/
```

### 10.3 Estrutura visível

```text
emails_bruno__20260805_143025/
├── PRONTO_PARA_IA/
│   ├── emails_parte_0001.json
│   ├── emails_parte_0002.json
│   └── emails_parte_0003.json
├── LEIA-ME.txt
└── relatorio_conversao.json
```

- `PRONTO_PARA_IA`: único diretório que o usuário precisa enviar ou integrar.
- `LEIA-ME.txt`: explicação simples do conteúdo, limitações e forma de uso.
- `relatorio_conversao.json`: informações técnicas, avisos, métricas e falhas.

Os arquivos originais permanecerão em seus locais de origem.

## 11. Perfis de destino

### 11.1 Plataforma de IA

Destinado a upload manual em ChatGPT ou plataforma semelhante.

- Dados estruturados: JSON particionado.
- Documentos narrativos: Markdown particionado.
- Limites conservadores de bytes e tokens.
- Arquivos independentes e numerados.

### 11.2 API/File Search

Destinado a pipelines técnicos e busca semântica.

- Dados estruturados: JSONL particionado.
- Documentos narrativos: Markdown particionado.
- Metadados de origem preservados.
- Limites configuráveis conforme a integração.

### 11.3 Personalizado

Permite selecionar formato, limite em bytes, limite estimado de tokens e opções
de conteúdo. Será apresentado como recurso avançado.

## 12. Seleção automática do formato

A opção padrão será `Automático (recomendado)`. A decisão será exibida antes da
conversão e poderá ser alterada.

| Fonte | Plataforma de IA | API/File Search | Justificativa |
|---|---|---|---|
| MBOX/EML | JSON | JSONL | Preserva campos e relacionamentos de e-mail |
| CSV/XLSX | JSON | JSONL | Preserva linhas, colunas, abas e tipos |
| JSON/JSONL | JSON normalizado | JSONL normalizado | Mantém dados estruturados |
| PDF | Markdown | Markdown | Preserva leitura, seções e referências de página |
| DOCX | Markdown | Markdown | Preserva títulos, listas, seções e tabelas simples |
| TXT | Markdown | Markdown | Formato textual eficiente para LLMs |
| Markdown | Markdown limpo | Markdown limpo | Já é apropriado para leitura semântica |
| Imagem com OCR | Markdown | Markdown | Representa texto reconhecido e sua origem |

## 13. Contratos de dados

### 13.1 Estratégia

Não haverá um único esquema interno para todos os documentos. Haverá:

- um envelope comum e versionado;
- um `record_type` que identifica o contrato;
- um bloco `data` específico para o tipo;
- um bloco `processing` com rastreabilidade.

```json
{
  "schema_version": "1.0",
  "record_type": "email_message",
  "record_id": "...",
  "source": {},
  "data": {},
  "processing": {}
}
```

### 13.2 Campos comuns

| Campo | Obrigatório | Descrição |
|---|---:|---|
| `schema_version` | Sim | Versão do contrato |
| `record_type` | Sim | Tipo discriminador do registro |
| `record_id` | Sim | Identificador estável dentro da conversão |
| `source.file_name` | Sim | Nome da fonte sem exigir o caminho completo |
| `source.file_type` | Sim | Formato identificado |
| `source.size_bytes` | Sim | Tamanho da fonte |
| `data` | Sim | Conteúdo específico do tipo |
| `processing.converted_at` | Sim | Data e hora da conversão |
| `processing.warnings` | Sim | Lista, possivelmente vazia, de avisos |

O caminho absoluto da fonte ficará apenas no relatório local, evitando expor
informações do computador nos arquivos enviados à IA.

### 13.3 Contrato `email_message`

Fontes: MBOX e EML. Um MBOX produzirá um registro por mensagem.

```json
{
  "schema_version": "1.0",
  "record_type": "email_message",
  "record_id": "email_abc123",
  "source": {
    "file_name": "emails_bruno.mbox",
    "file_type": "mbox",
    "size_bytes": 2851969403
  },
  "data": {
    "message_id": "<abc123@example.com>",
    "thread_id": "1674020694403003387",
    "gmail_labels": ["Caixa de entrada"],
    "date": "2020-08-18T15:17:46-03:00",
    "from": [],
    "to": [],
    "cc": [],
    "bcc": [],
    "reply_to": [],
    "in_reply_to": null,
    "references": [],
    "subject": "Assunto",
    "body_text": "Texto integral do e-mail",
    "body_analysis": "Texto preparado para análise",
    "attachments": [
      {
        "file_name": "ata.pdf",
        "media_type": "application/pdf",
        "size_bytes": 123456,
        "content_extracted": false
      }
    ]
  },
  "processing": {
    "converted_at": "2026-08-05T14:30:25-03:00",
    "unicode_cleaned": true,
    "warnings": []
  }
}
```

Requisitos específicos:

- preservar labels e identificadores de thread quando disponíveis;
- preservar `In-Reply-To` e `References`;
- manter corpo integral e, futuramente, corpo preparado para análise;
- catalogar anexos sem incorporar binários em Base64;
- declarar explicitamente se o conteúdo do anexo foi extraído;
- permitir segmentação de uma mensagem excepcionalmente grande;
- registrar problemas de codificação por mensagem.

### 13.4 Contrato `pdf_document`

Fonte: PDF. O texto preservará referências de página.

```json
{
  "schema_version": "1.0",
  "record_type": "pdf_document",
  "record_id": "pdf_def456",
  "source": {
    "file_name": "estatuto.pdf",
    "file_type": "pdf",
    "size_bytes": 845000
  },
  "data": {
    "title": "Estatuto da Liga",
    "author": null,
    "page_count": 12,
    "pages": [
      {
        "page_number": 1,
        "text": "Texto da primeira página",
        "extraction_method": "embedded_text"
      }
    ],
    "outline": [],
    "embedded_files": [],
    "images": []
  },
  "processing": {
    "converted_at": "2026-08-05T14:30:25-03:00",
    "ocr_applied": false,
    "warnings": []
  }
}
```

Na saída Markdown, o mesmo contrato conceitual será representado com metadados
iniciais e marcadores explícitos de página.

### 13.5 Contratos planejados

- `word_document`: títulos, seções, parágrafos, listas e tabelas.
- `spreadsheet_workbook`: abas, intervalos, tabelas, colunas, linhas e tipos.
- `tabular_dataset`: cabeçalhos, linhas, tipos inferidos e delimitador.
- `text_document`: conteúdo, codificação, títulos e seções detectadas.
- `structured_data`: estrutura normalizada e caminho lógico dos registros.
- `image_document`: texto de OCR, idioma, confiança e regiões, em fase futura.

Cada contrato deverá possuir seu próprio JSON Schema e testes de validação antes
de ser considerado estável.

## 14. Limpeza e preparação

### 14.1 Regras gerais

- Normalizar Unicode em NFC.
- Substituir espaços não separáveis por espaços normais.
- Remover caracteres invisíveis e controles desnecessários.
- Preservar acentos, emojis e pontuação válida.
- Converter separadores Unicode em quebras de linha.
- Detectar, sem corrigir agressivamente, possíveis problemas de codificação.
- Registrar quantidade e tipo de alterações.

### 14.2 Limpeza semântica

O conteúdo original extraído não será apagado. Quando houver remoção de
assinaturas, históricos citados ou elementos repetitivos, o aplicativo manterá:

- `body_text`: texto integral extraído;
- `body_analysis`: versão opcional preparada para análise.

Essa função será posterior ao MVP e deverá ser conservadora.

### 14.3 Dados pessoais

A aplicação deverá detectar padrões prováveis de:

- endereços de e-mail;
- telefones;
- CPF;
- endereços e outros identificadores quando tecnicamente viável.

O relatório apresentará contagens aproximadas. A anonimização será opcional e
deverá explicar que detecção automática não oferece garantia absoluta.

## 15. Particionamento

### 15.1 Requisitos

- Considerar simultaneamente bytes e tokens estimados.
- Nunca carregar toda a fonte na memória quando o formato permitir streaming.
- Evitar dividir uma unidade lógica entre partes.
- Se uma unidade exceder o limite, segmentar seu conteúdo e preservar o vínculo.
- Gerar nomes numerados em ordem determinística.
- Produzir arquivos individualmente válidos.

### 15.2 Perfil inicial para plataforma

- Limite físico conservador configurável.
- Limite padrão de aproximadamente 500 mil tokens estimados por parte.
- Estimativa conservadora quando não houver tokenizador específico.
- Limites externos não serão codificados como permanentes; deverão ser
  configuráveis e documentados por versão do aplicativo.

## 16. Relatório e LEIA-ME

### 16.1 `LEIA-ME.txt`

Será escrito em linguagem simples e informará:

- arquivos processados;
- formato da saída;
- quantidade de partes;
- o que está incluído;
- o que não está incluído;
- presença de anexos não extraídos;
- instrução para enviar os arquivos de `PRONTO_PARA_IA`;
- alerta sobre dados pessoais.

### 16.2 `relatorio_conversao.json`

Deverá conter:

- identificador da conversão;
- início, término e duração;
- fontes, caminhos locais, tamanhos e datas de modificação;
- formato detectado e contrato usado;
- perfil e formato de saída;
- configurações de particionamento;
- contagens de registros, partes, avisos e falhas;
- normalizações realizadas;
- conteúdo omitido ou não extraído;
- possíveis dados pessoais;
- lista de arquivos gerados;
- resultado final: sucesso, sucesso com avisos ou falha.

## 17. Requisitos funcionais

| ID | Requisito |
|---|---|
| RF-001 | Selecionar um ou vários arquivos locais |
| RF-002 | Identificar automaticamente formatos suportados |
| RF-003 | Recomendar formato de saída com justificativa visível |
| RF-004 | Permitir substituir a recomendação automática |
| RF-005 | Usar Downloads como destino padrão |
| RF-006 | Permitir escolher outro destino |
| RF-007 | Criar uma pasta única por conversão sem sobrescrever resultados |
| RF-008 | Aplicar o contrato correspondente ao tipo da fonte |
| RF-009 | Limpar Unicode e registrar as alterações |
| RF-010 | Particionar por bytes e tokens estimados |
| RF-011 | Mostrar progresso durante a conversão |
| RF-012 | Permitir cancelamento seguro |
| RF-013 | Gerar `PRONTO_PARA_IA`, `LEIA-ME.txt` e relatório |
| RF-014 | Abrir diretamente a pasta de resultados |
| RF-015 | Avisar sobre possíveis conversões repetidas |
| RF-016 | Preservar e não modificar os arquivos originais |
| RF-017 | Continuar processando outros arquivos após uma falha isolada |
| RF-018 | Manter uma interface de linha de comando para uso técnico |

## 18. Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF-001 | Processamento totalmente local por padrão |
| RNF-002 | Memória aproximadamente constante em fontes compatíveis com streaming |
| RNF-003 | Compatibilidade inicial com Windows 10 e 11 |
| RNF-004 | Interface utilizável sem conhecimento técnico |
| RNF-005 | Saídas em UTF-8 |
| RNF-006 | Nenhuma sobrescrita silenciosa |
| RNF-007 | Erros devem identificar fonte e etapa sem expor conteúdo no log |
| RNF-008 | Contratos de dados versionados |
| RNF-009 | Conversores independentes e testáveis |
| RNF-010 | Aplicação distribuível sem exigir instalação manual de Python |

## 19. Arquitetura proposta

```text
Aplicação desktop
├── Interface
│   ├── Seleção e configuração
│   ├── Progresso e cancelamento
│   └── Resumo e abertura da saída
├── Orquestrador de conversão
│   ├── Detecção de formato
│   ├── Seleção de contrato
│   ├── Seleção de perfil
│   └── Relatório
├── Núcleo
│   ├── Limpeza Unicode
│   ├── Particionamento
│   ├── Estimativa de tokens
│   ├── Privacidade
│   └── Escrita atômica
├── Conversores
│   ├── MBOX/EML
│   ├── PDF
│   ├── DOCX
│   ├── TXT/Markdown
│   ├── CSV/XLSX
│   └── JSON/JSONL
└── Saídas
    ├── JSON
    ├── JSONL
    └── Markdown
```

O conversor MBOX existente deverá ser refatorado para usar o núcleo comum, sem
perder a compatibilidade da CLI.

## 20. Estado atual validado

Em 19 de agosto de 2026, as Fases 1 a 4 estão implementadas no novo projeto.
Foram validados:

- núcleo modular, contratos versionados, CLI e interface desktop;
- MBOX real de aproximadamente 2,66 GiB, com 3.699 mensagens sem falhas;
- progresso, cancelamento seguro, saída automática em Downloads e prevenção de
  sobrescrita silenciosa;
- TXT e Markdown particionados;
- PDF com referências explícitas de página;
- DOCX com estrutura, tabelas simples e inferências conservadoras;
- CSV real com 113.036 linhas, dividido em 19 partes sem perdas, falhas ou
  inconsistências de tipos;
- XLSX real com aba, intervalo, cabeçalhos e tipos preservados, validado pelo
  JSON Schema `spreadsheet_workbook@1.0`;
- 101 testes automatizados aprovados, além de análise estática e compilação.

Limites atuais conhecidos:

- a interface seleciona uma fonte por conversão; seleção múltipla permanece
  planejada;
- conteúdo binário de anexos não é extraído;
- OCR e anonimização ainda não foram implementados;
- `.xls` legado não é aceito;
- fórmulas XLSX não são executadas e dependem do valor em cache quando existente;
- planilhas XLSX muito grandes ainda precisam de teste específico de memória;
- o layout desktop é funcional, mas o refinamento visual final pertence à fase
  de distribuição.

## 21. Roadmap

### Fase 1 — Núcleo e contrato de e-mail — concluída

- Refatorar o conversor atual em módulos.
- Definir JSON Schema do `email_message`.
- Incluir labels e threads do Gmail.
- Incluir `In-Reply-To` e `References`.
- Adicionar progresso e cancelamento.
- Adaptar a saída para `PRONTO_PARA_IA` e `LEIA-ME.txt`.
- Manter a CLI funcional.

### Fase 2 — MVP desktop — concluída

- Implementar interface Tkinter/ttk.
- Detectar a pasta Downloads do sistema.
- Selecionar arquivos e perfil.
- Exibir recomendação automática.
- Executar conversão em segundo plano.
- Mostrar progresso, avisos e resumo.
- Abrir a pasta de saída.

### Fase 3 — Documentos narrativos — concluída

- Implementar TXT e Markdown.
- Implementar PDF com referências de página.
- Implementar DOCX com seções e tabelas simples.
- Criar contratos e testes correspondentes.

### Fase 4 — Dados tabulares — concluída

- Implementar CSV.
- Implementar XLSX com abas, tipos e tabelas.
- Gerar JSON ou JSONL conforme perfil.

### Fase 5 — Privacidade — próxima

- Detectar possíveis dados pessoais.
- Oferecer anonimização opcional.

### Fase 6 — Distribuição

- Criar executável Windows.
- Avaliar versão portátil e instalador.
- Adicionar identidade visual da LIMEBH.
- Testar em máquina sem Python.
- Criar manual curto para usuários.
- Definir versão, atualização e suporte.

### Evoluções futuras — fora do escopo atual

- Avaliar `body_analysis` conservador para e-mails.
- Avaliar extração do conteúdo de anexos.
- Avaliar OCR de imagens e PDFs digitalizados.

## 22. Critérios de aceite do MVP

O MVP será considerado pronto quando:

1. Um usuário sem terminal conseguir selecionar um MBOX e convertê-lo.
2. O arquivo original permanecer inalterado.
3. A aplicação criar automaticamente a pasta em Downloads.
4. A saída usar o contrato `email_message` versionado.
5. Labels, threads e relações de resposta forem preservadas quando existirem.
6. Os arquivos forem divididos dentro dos limites configurados.
7. O progresso for visível e o cancelamento não corromper resultados concluídos.
8. A pasta `PRONTO_PARA_IA` contiver apenas arquivos destinados ao uso com IA.
9. O `LEIA-ME.txt` explicar claramente inclusões e limitações.
10. O relatório registrar sucessos, avisos, falhas e transformações.
11. A conversão real de referência processar as 3.699 mensagens sem perda.
12. Os testes automatizados e uma validação visual da interface passarem.

## 23. Métricas de sucesso

- Percentual de mensagens/documentos convertidos sem falha.
- Tempo total de conversão por tamanho de fonte.
- Pico de memória em arquivos grandes.
- Quantidade de intervenções técnicas necessárias por conversão.
- Percentual de usuários que concluem sem consultar instruções externas.
- Quantidade de avisos compreendidos e resolvidos pelo usuário.
- Utilidade percebida dos arquivos nas análises da Liga.

## 24. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Exposição de dados pessoais | Processamento local, alertas e anonimização opcional |
| Perda semântica durante limpeza | Preservar texto integral e registrar transformações |
| Arquivos maiores que a memória | Streaming e escrita incremental |
| Limites externos mudarem | Perfis configuráveis e versionados |
| Formatos corrompidos ou incomuns | Avisos por registro e continuidade controlada |
| Anexo importante não extraído | Declarar `content_extracted: false` e informar no LEIA-ME |
| Repetição em históricos de e-mail | Futuro `body_analysis`, mantendo `body_text` |
| Decisão automática inadequada | Exibir justificativa e permitir alteração |
| Aplicativo parecer travado | Progresso desde a varredura inicial e mensagens de etapa |

## 25. Decisões registradas

- O produto será orientado à preparação para LLMs, não ao arquivamento.
- A pasta Downloads será o destino padrão.
- A saída será simples e conterá `PRONTO_PARA_IA`, `LEIA-ME.txt` e relatório.
- Os originais não serão copiados para a saída.
- Cada tipo de fonte terá seu próprio contrato.
- O contrato terá envelope comum e versão explícita.
- O modo automático recomendará JSON, JSONL ou Markdown.
- A recomendação será visível, explicada e substituível.
- E-mails e dados tabulares priorizarão formatos estruturados.
- Documentos narrativos priorizarão Markdown.
- O aplicativo não enviará dados automaticamente a serviços externos.
- A primeira interface será desktop, não Streamlit.
- `body_analysis`, extração de anexos e OCR ficam adiados para uma possível
  evolução futura e não fazem parte da Fase 5.

## 26. Questões em aberto

Estas decisões serão tomadas durante as fases correspondentes:

- Nome público definitivo e identidade visual do aplicativo.
- Formatos e plataformas exatas suportadas por cada perfil de destino.
- Dependências para PDF, DOCX e XLSX.
- Estratégia de tokenização exata ou conservadora por modelo.
- Nível padrão de detecção ou anonimização de dados pessoais.
- Formato de atualização e distribuição do executável.
- Necessidade de assinatura digital do aplicativo Windows.

## 27. Próximo incremento

O próximo incremento será o planejamento da Fase 5, agora restrita à privacidade.
Antes de codificar, o escopo será dividido em entregas pequenas, começando pela
detecção auditável de possíveis dados pessoais e sua apresentação no relatório.
A anonimização opcional será tratada em incremento posterior da mesma fase.
`body_analysis`, extração de anexos e OCR ficam fora do escopo atual.
