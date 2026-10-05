# Manual rápido — Preparador de Dados para IA 0.1.0

O Preparador de Dados para IA transforma arquivos em formatos mais adequados
para leitura por plataformas de inteligência artificial. Todo o processamento é
feito no seu computador, sem envio automático pela internet.

## Como executar

1. Descompacte o arquivo ZIP por completo.
2. Abra a pasta `Preparador de Dados para IA`.
3. Execute `Preparador de Dados para IA.exe`.

Não mova apenas o executável. A pasta `_internal` precisa permanecer ao lado dele.

Se o Windows exibir um alerta do SmartScreen, confirme a abertura somente se o
arquivo tiver vindo de uma fonte confiável.

## Como preparar um arquivo

As configurações que aparecem ao abrir o aplicativo já são as recomendadas para
o usuário comum. Normalmente, você não precisa alterar nada.

1. Clique em **Adicionar arquivo**.
2. Escolha o arquivo que deseja preparar.
3. Confira o nome e o caminho mostrados em **Arquivo de origem**.
4. Mantenha **Destino de uso** como **Plataforma de IA**. O aplicativo escolherá
   automaticamente o formato de saída mais apropriado para o tipo de arquivo.
5. Mantenha o **Destino local** sugerido, salvo se quiser guardar o resultado em
   outra pasta.
6. Clique em **Iniciar conversão**.
7. Aguarde a conclusão. Arquivos grandes, especialmente MBOX, podem levar mais
   tempo.
8. Clique em **Abrir arquivos prontos** para acessar o material preparado.

Durante uma conversão, o botão **Cancelar** interrompe o processamento com
segurança. Se já existir uma pasta com o mesmo nome, aceite a criação de uma nova
pasta para não substituir resultados anteriores.

## Configurações disponíveis

- **Destino de uso:** mantenha **Plataforma de IA** para uso comum e envio manual
  dos arquivos. A opção de API destina-se a integrações técnicas.
- **Formato automático:** é definido pelo aplicativo conforme o arquivo de
  origem e não exige escolha manual.
- **Destino local:** indica onde a nova pasta será criada. O padrão é a pasta de
  Downloads do usuário.
- **Limpeza Unicode e relatório:** já ficam ativados conforme as recomendações
  do aplicativo.
- **Preservar também o HTML:** é opcional para arquivos MBOX. Deixe desmarcado,
  a menos que você realmente precise manter a versão HTML dos e-mails.

## Formatos aceitos

- MBOX
- TXT e Markdown
- PDF com texto incorporado
- DOCX
- CSV
- XLSX

## Onde ficam os resultados

Por padrão, cada conversão cria uma pasta dentro de:

```text
Downloads\Preparador de Dados para IA
```

Cada conversão recebe sua própria pasta, identificada pelo nome do arquivo e pela
data e hora. Dentro dela:

- `PRONTO_PARA_IA` contém os arquivos que devem ser enviados à plataforma de IA;
- `relatorio_conversao.json` registra informações técnicas da conversão;
- `LEIA-ME.txt` resume o conteúdo gerado e eventuais limitações.

Para o uso comum, abra `PRONTO_PARA_IA` e envie suas partes em ordem numérica.
Se houver várias partes, elas foram divididas para manter um tamanho adequado às
plataformas de IA.

## Em caso de avisos

Um aviso não significa necessariamente que a conversão falhou. Ele pode indicar,
por exemplo, alguma estrutura incomum no documento. Use **Abrir relatório** para
consultar os detalhes. Se o aplicativo informar uma falha, confirme se o arquivo
abre normalmente no programa de origem e tente novamente.

## Privacidade e limitações

- Todo o processamento ocorre localmente.
- O aplicativo não envia arquivos automaticamente à internet.
- A saída pode conter dados pessoais presentes no documento original.
- OCR, extração do conteúdo de anexos e anonimização não fazem parte desta versão.
- Arquivos `.xls` antigos não são aceitos; use `.xlsx`.
