"""Gera os PDFs artificiais usados nos testes da fase 3C."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject, TextStringObject
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

OUTPUT = Path(__file__).with_name("artificial_document.pdf")
WIDTH, HEIGHT = A4


def _scanned_page_image() -> BytesIO:
    image = Image.new("RGB", (1200, 1600), "#f7f3e8")
    drawing = ImageDraw.Draw(image)
    drawing.rectangle((85, 80, 1115, 1520), outline="#126b5b", width=8)
    drawing.rectangle((120, 130, 1080, 300), fill="#d8eee7")
    drawing.text((170, 185), "PAGINA DIGITALIZADA ARTIFICIAL", fill="#123b35")
    drawing.text((170, 390), "Esta pagina contem apenas uma imagem raster.", fill="#263d39")
    drawing.text((170, 445), "O preparador deve cataloga-la sem aplicar OCR.", fill="#263d39")
    drawing.line((170, 535, 1030, 535), fill="#87a69f", width=4)
    drawing.text((170, 600), "Documento de teste - nenhum dado real.", fill="#516862")
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output


def _draw_header(pdf: canvas.Canvas, section: str) -> None:
    pdf.setFillColor(colors.HexColor("#0a3d35"))
    pdf.rect(0, HEIGHT - 56, WIDTH, 56, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(42, HEIGHT - 35, "LIMEBH - DOCUMENTO ARTIFICIAL")
    pdf.drawRightString(WIDTH - 42, HEIGHT - 35, section)


def _base_pdf() -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=1, invariant=1)
    pdf.setTitle("Relatorio Artificial da Fase 3C")
    pdf.setAuthor("LIMEBH")
    pdf.setSubject("Fixture artificial para validacao local de PDF")

    pdf.bookmarkPage("visao_geral")
    pdf.addOutlineEntry("Visao geral", "visao_geral", level=0)
    _draw_header(pdf, "1 / 3")
    pdf.setFillColor(colors.HexColor("#102f2a"))
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawString(54, HEIGHT - 115, "Relatorio Artificial da Fase 3C")
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.HexColor("#425c56"))
    pdf.drawString(54, HEIGHT - 145, "Amostra local para validar extracao e estrutura por pagina.")
    pdf.setFillColor(colors.HexColor("#dceee9"))
    pdf.roundRect(54, HEIGHT - 250, WIDTH - 108, 66, 8, stroke=0, fill=1)
    pdf.setFillColor(colors.HexColor("#0a3d35"))
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(72, HEIGHT - 214, "Objetivo")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(145, HEIGHT - 214, "Confirmar texto, metadados, sumario e limites de pagina.")
    pdf.setStrokeColor(colors.HexColor("#9db8b1"))
    pdf.line(54, HEIGHT - 300, WIDTH - 54, HEIGHT - 300)
    pdf.setFillColor(colors.HexColor("#243d38"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(54, HEIGHT - 330, "Campo")
    pdf.drawString(245, HEIGHT - 330, "Valor artificial")
    pdf.setFont("Helvetica", 11)
    for row, (label, value) in enumerate(
        (("Origem", "ambiente local"), ("Perfil", "plataforma de IA"), ("OCR", "nao aplicado"))
    ):
        y = HEIGHT - 360 - row * 28
        pdf.drawString(54, y, label)
        pdf.drawString(245, y, value)
    pdf.showPage()

    pdf.bookmarkPage("procedimentos")
    pdf.addOutlineEntry("Procedimentos", "procedimentos", level=0)
    pdf.bookmarkPage("controles")
    pdf.addOutlineEntry("Controles", "controles", level=1)
    _draw_header(pdf, "2 / 3")
    pdf.setFillColor(colors.HexColor("#102f2a"))
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(54, HEIGHT - 115, "Procedimentos de validacao")
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.HexColor("#334f49"))
    lines = (
        "1. Extrair o texto incorporado sem alterar o arquivo de origem.",
        "2. Preservar a referencia explicita da pagina no Markdown.",
        "3. Catalogar imagens e anexos sem copiar seus conteudos binarios.",
        "4. Registrar avisos quando uma pagina nao possuir texto extraivel.",
    )
    for index, line in enumerate(lines):
        pdf.drawString(64, HEIGHT - 165 - index * 34, line)
    pdf.setFillColor(colors.HexColor("#edf5f2"))
    pdf.roundRect(54, HEIGHT - 390, WIDTH - 108, 88, 8, stroke=0, fill=1)
    pdf.setFillColor(colors.HexColor("#0a3d35"))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(72, HEIGHT - 330, "Controle de privacidade")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(
        72, HEIGHT - 355, "Nenhum conteudo desta amostra representa pessoa ou operacao real."
    )
    pdf.showPage()

    pdf.bookmarkPage("pagina_digitalizada")
    pdf.addOutlineEntry("Pagina digitalizada", "pagina_digitalizada", level=0)
    scanned = _scanned_page_image()
    pdf.drawImage(ImageReader(scanned), 0, 0, width=WIDTH, height=HEIGHT, mask="auto")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def create_fixture(output: Path = OUTPUT) -> Path:
    reader = PdfReader(BytesIO(_base_pdf()))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    attachment_data = b"Fixture artificial da fase 3C. Nenhum dado real.\n"
    attachment = writer.add_attachment("notas_artificiais.txt", attachment_data)
    attachment.subtype = NameObject("/text#2Fplain")
    attachment.size = NumberObject(len(attachment_data))
    attachment.description = TextStringObject("Notas artificiais para teste de catalogacao")
    with output.open("wb") as stream:
        writer.write(stream)
    return output


if __name__ == "__main__":
    print(create_fixture())
