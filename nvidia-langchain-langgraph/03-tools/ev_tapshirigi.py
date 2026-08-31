from langchain_core.tools import tool


@tool
def vergi_hesabla(məbləğ: float, faiz: float) -> float:
    """Verilən məbləğ və vergi faizindən vergi məbləğini hesablayıb qaytarır.

    İstifadəçi vergi tutarını hesablamaq istədikdə bu tool-dan istifadə et.
    məbləğ: verginin hesablanacağı məbləğ (məsələn 200)
    faiz: vergi faizi (məsələn 18)
    """
    return məbləğ * faiz / 100


@tool
def endirim_tətbiq_et(qiymət: float, faiz: float):
    """Verilən qiymətə endirim faizi tətbiq edib yekun qiyməti qaytarır.

    İstifadəçi endirimdən sonrakı qiyməti hesablamaq istədikdə bu tool-dan istifadə et.
    qiymət: ilkin qiymət (məsələn 100)
    faiz: endirim faizi (məsələn 20)
    """
    try:
        if faiz > 100:
            return "Xəta: Endirim 100 faizdən çox ola bilməz."
        nəticə = qiymət * (1 - faiz / 100)
        return nəticə
    except Exception:
        return "Xəta: Endirim 100 faizdən çox ola bilməz."


hesab_toolkit = [vergi_hesabla, endirim_tətbiq_et]


if __name__ == "__main__":
    print(vergi_hesabla.invoke({"məbləğ": 200, "faiz": 18}))
    print(endirim_tətbiq_et.invoke({"qiymət": 100, "faiz": 20}))
    print(endirim_tətbiq_et.invoke({"qiymət": 100, "faiz": 150}))

    for t in hesab_toolkit:
        print(t.name)
