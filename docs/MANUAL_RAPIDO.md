# Preparador de Dados para IA 0.1.0 — versão portátil

## Como executar

1. Descompacte o arquivo ZIP por completo.
2. Abra a pasta `Preparador de Dados para IA`.
3. Execute `Preparador de Dados para IA.exe`.
4. Selecione um arquivo e inicie a conversão.
5. Use o botão do resultado para abrir os arquivos preparados.

Não mova apenas o executável. A pasta `_internal` precisa permanecer ao lado dele.

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

Somente os arquivos de `PRONTO_PARA_IA` devem ser enviados à plataforma de IA.
O relatório e o `LEIA-ME.txt` registram detalhes técnicos e limitações.

## Privacidade e limitações

- Todo o processamento ocorre localmente.
- O aplicativo não envia arquivos automaticamente à internet.
- A saída pode conter dados pessoais presentes no documento original.
- OCR, extração do conteúdo de anexos e anonimização não fazem parte desta versão.
- Arquivos `.xls` antigos não são aceitos; use `.xlsx`.

Como esta versão ainda não possui assinatura digital, o Windows pode exibir um
alerta do SmartScreen ao iniciá-la em outro computador.
