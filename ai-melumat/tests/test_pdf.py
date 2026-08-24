from pathlib import Path

from pypdf import PdfReader


def test_pdf_extracts_contract_terms():
    pdf = Path(__file__).resolve().parent.parent / "fixtures" / "muqavile.pdf"
    text = "\n".join((p.extract_text() or "") for p in PdfReader(str(pdf)).pages)
    assert "500 AZN" in text
    assert "12 ay" in text
