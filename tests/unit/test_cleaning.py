from limebh_preparador.core.cleaning import UnicodeSanitizer, html_to_text, sanitize_record


def test_unicode_cleanup_preserves_valid_content() -> None:
    sanitizer = UnicodeSanitizer()
    record = sanitize_record(
        {"body_text": "Olá\u00a0Liga\u200b — música 🎵\u2028nova linha\u202d"},
        sanitizer,
    )

    assert record == {"body_text": "Olá Liga — música 🎵\nnova linha"}
    assert sanitizer.report()["total_changes"] == 4


def test_html_to_text_preserves_blocks() -> None:
    assert html_to_text("<p>Primeira</p><p>Segunda &amp; última</p>") == (
        "Primeira\n\nSegunda & última"
    )
