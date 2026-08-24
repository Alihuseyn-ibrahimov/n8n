"""OCR nümunəsi — şəkildəki mətni oxumaq (tesseract lazımdır).

Quraşdırma (Linux):
  sudo apt-get install -y tesseract-ocr
  pip install pytesseract pillow

Azərbaycan paketi:
  sudo curl -L -o /usr/local/share/tessdata/aze.traineddata \\
    https://github.com/tesseract-ocr/tessdata/raw/main/aze.traineddata
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "hesab.png"


def ensure_receipt() -> Path:
    if FIXTURE.exists():
        return FIXTURE
    img = Image.new("RGB", (420, 220), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((24, 24), "QEBZ / RECEIPT", fill="black", font=font)
    draw.text((24, 70), "Corek   2 AZN", fill="black", font=font)
    draw.text((24, 100), "Sud     3 AZN", fill="black", font=font)
    draw.text((24, 150), "CEM     5 AZN", fill="black", font=font)
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    img.save(FIXTURE)
    return FIXTURE


def sekilden_metn(sekil_yolu: str | Path, lang: str = "eng") -> str:
    import pytesseract

    sekil = Image.open(sekil_yolu)
    return pytesseract.image_to_string(sekil, lang=lang)


if __name__ == "__main__":
    yol = ensure_receipt()
    try:
        print(sekilden_metn(yol))
    except Exception as err:
        print("OCR işləmədi (tesseract quraşdırılmayıb ola bilər):", err)
        print("Şəkil hazırdır:", yol)
