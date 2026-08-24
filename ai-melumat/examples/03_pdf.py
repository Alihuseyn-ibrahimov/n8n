"""Mətnli PDF-dən mətn çıxarmaq (pypdf)."""

from pathlib import Path

from pypdf import PdfReader

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "muqavile.pdf"


def pdf_metn(pdf_yolu: str | Path) -> str:
    oxuyucu = PdfReader(str(pdf_yolu))
    hisseler = []
    for sehife in oxuyucu.pages:
        hisseler.append(sehife.extract_text() or "")
    return "\n".join(hisseler).strip()


if __name__ == "__main__":
    print(pdf_metn(FIXTURE))
