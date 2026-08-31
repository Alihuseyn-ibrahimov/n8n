"""
Ev tapşırığı — Example Code (3)

İki tool yarat və onları bir toolkit-ə yığ:
1. vergi_hesabla  — məbləğ və faizdən vergi məbləğini hesabla
2. endirim_tətbiq_et — qiymətə endirim tətbiq et; faiz 100-dən böyükdürsə xəta qaytar
"""

from langchain_core.tools import tool


@tool
def vergi_hesabla(məbləğ: float, faiz: float) -> float:
    """Məbləğ üzrə vergi məbləğini hesablayır.

    İstifadəçi vergi tutarını öyrənmək istədikdə bu tool-dan istifadə et.
    məbləğ: verginin hesablanacağı əsas məbləğ (məsələn 200.0)
    faiz: vergi faizi (məsələn 18.0)
    Qaytarır: vergi məbləği = məbləğ * faiz / 100
    """
    return məbləğ * faiz / 100


@tool
def endirim_tətbiq_et(qiymət: float, faiz: float) -> float | str:
    """Qiymətə endirim faizi tətbiq edib yekun qiyməti qaytarır.

    İstifadəçi endirimdən sonrakı qiyməti öyrənmək istədikdə bu tool-dan istifadə et.
    qiymət: ilkin qiymət (məsələn 100.0)
    faiz: endirim faizi, 0-100 aralığında (məsələn 20.0)
    Əgər faiz 100-dən böyükdürsə, çökmək əvəzinə aydın xəta mesajı qaytarılır.
    """
    try:
        if faiz > 100:
            return "Xəta: Endirim 100 faizdən çox ola bilməz."
        return qiymət * (1 - faiz / 100)
    except Exception as e:
        return f"Xəta: Endirim hesablana bilmədi. {e}"


hesab_toolkit = [vergi_hesabla, endirim_tətbiq_et]


def main() -> None:
    print(vergi_hesabla.invoke({"məbləğ": 200, "faiz": 18}))
    print(endirim_tətbiq_et.invoke({"qiymət": 100, "faiz": 20}))
    print(endirim_tətbiq_et.invoke({"qiymət": 100, "faiz": 150}))
    print()

    for t in hesab_toolkit:
        print(t.name)


if __name__ == "__main__":
    main()
