# Validação da Fase 3B — TXT e Markdown

Data da validação: 6 de agosto de 2026.

## Escopo concluído

O incremento 3B implementa a conversão real de documentos TXT e Markdown:

- seleção pela CLI e pela interface desktop;
- despacho pelo registro comum criado no 3A;
- leitura local sem alterar a fonte;
- detecção conservadora de codificação;
- normalização Unicode auditável;
- detecção de títulos e seções;
- construção e validação do contrato `text_document@1.0`;
- representação final em Markdown com metadados iniciais;
- particionamento simultâneo por bytes e tokens estimados;
- progresso, cancelamento e relatório no fluxo já usado pelo MBOX.

O comportamento do MBOX foi preservado. Um novo despachante escolhe o conversor
pela extensão e mantém o núcleo de e-mail existente como caminho especializado.

## Codificação

Arquivos com BOM UTF-8, UTF-16 ou UTF-32 são reconhecidos explicitamente. Sem
BOM, UTF-8 estrito é tentado antes de `charset-normalizer`. Em codificações de
um byte ambíguas, a presença de uma alternativa Windows-1252 recebe preferência
transparente por ser comum em documentos administrativos brasileiros; essa
decisão gera o aviso `encoding_ambiguous_windows_1252_preferred`.

O leitor consulta o token de cancelamento entre blocos de 1 MiB. Para permitir a
análise estrutural do incremento inicial, o conteúdo textual decodificado ainda
é mantido em memória. Uma estratégia de segmentação totalmente em fluxo poderá
ser acrescentada quando arquivos narrativos reais justificarem essa
complexidade, sem alterar o contrato.

## Estrutura textual

Markdown é analisado com `markdown-it-py`, o que evita interpretar marcadores
dentro de blocos de código como títulos. TXT usa heurísticas conservadoras para:

- títulos com `#`;
- títulos sublinhados com `===` ou `---`;
- numeração hierárquica, como `1.` e `1.2.`;
- linhas curtas em maiúsculas, isoladas por linhas vazias.

Cada título registra nível e linha. As seções preservam título, nível, intervalo
de linhas e conteúdo.

## Saída Markdown

Cada parte `.md` é autossuficiente e começa com metadados em front matter:

- versão e tipo do contrato;
- identificador estável;
- nome, tipo e tamanho da fonte, sem caminho absoluto;
- codificação e formato do conteúdo;
- data de conversão e estado da limpeza Unicode;
- intervalo de linhas do conteúdo;
- avisos e informações de segmentação, quando aplicáveis.

TXT é representado como Markdown, promovendo títulos detectados. Markdown de
origem é preservado após a limpeza Unicode. O particionador prefere limites de
parágrafo, linha e palavra; se uma unidade excepcional exceder os limites, as
partes mantêm o mesmo `record_id` e recebem número e total de segmentos.

## Integração desktop e CLI

A janela agora aceita `.mbox`, `.txt`, `.md` e `.markdown`. A recomendação passa
a depender também da fonte:

- MBOX continua em JSON para plataforma e JSONL para API;
- TXT e Markdown geram Markdown para ambos os perfis.

A opção de preservar HTML fica disponível somente para MBOX. Contadores,
resumos e mensagens de progresso distinguem mensagens de documentos.

## Segurança e rastreabilidade

- a fonte permanece no local original e seu hash não muda nos testes;
- o caminho absoluto aparece somente no relatório local;
- nenhum endereço externo ou referência é baixado;
- saídas temporárias incompletas não permanecem após cancelamento;
- problemas de extração registram apenas etapa e tipo de erro, sem conteúdo.

## Validação automatizada

A suíte cobre:

- UTF-8 com BOM e documentos Windows-1252 em português;
- cancelamento durante a leitura;
- títulos e seções de TXT;
- títulos Markdown sem falsos positivos em blocos de código;
- conformidade com `text_document.schema.json`;
- front matter, promoção de títulos e ausência de caminho absoluto;
- partes Markdown independentes dentro dos limites de bytes e tokens;
- integração completa pela CLI e pelo worker da interface;
- regressão do conversor MBOX.

Também são executadas análise estática, verificação de formatação e compilação.

## Fora do escopo

PDF e DOCX ainda não são selecionáveis. Seus contratos permanecem prontos no
3A e serão implementados nos próximos incrementos da Fase 3. OCR, remoção
semântica de assinaturas e download de referências externas também permanecem
fora deste incremento.
