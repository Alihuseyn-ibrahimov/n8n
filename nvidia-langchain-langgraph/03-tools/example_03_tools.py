"""
Example Code (3)
LangChain Tools — @tool, təsvir, Pydantic, xəta idarəetməsi və toolkit

Bu skript dərsin bütün nümunələrini ardıcıl işlədir.
İşə salmaq: python example_03_tools.py
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 2. Ən sadə tool: @tool dekoratoru
# ---------------------------------------------------------------------------

@tool
def hərfləri_say(mətn: str) -> int:
    """Verilən mətndəki hərflərin sayını qaytarır."""
    return len(mətn)


# ---------------------------------------------------------------------------
# 3. Tool-un təsviri — model üçün aydın yazılmalıdır
# ---------------------------------------------------------------------------

@tool
def valyuta_çevir(məbləğ: float) -> float:
    """Dolları manata çevirir.

    İstifadəçi dolları manata çevirmək istədikdə bu tool-dan istifadə et.
    məbləğ: çevriləcək dollar miqdarı (məsələn 100.0)
    """
    usd_azn = 1.70
    return məbləğ * usd_azn


# ---------------------------------------------------------------------------
# 4. Giriş məlumatlarını yoxlamaq (Pydantic)
# ---------------------------------------------------------------------------

class HavaSorğusu(BaseModel):
    şəhər: str = Field(description="Havası öyrəniləcək şəhərin adı, məsələn 'Bakı'")


@tool(args_schema=HavaSorğusu)
def havanı_yoxla(şəhər: str) -> str:
    """Verilən şəhər üçün hava proqnozunu qaytarır."""
    return f"{şəhər} üçün proqnoz: Günəşli, 25 dərəcə"


# ---------------------------------------------------------------------------
# 5. Xəta idarəetməsi (Error Handling)
# ---------------------------------------------------------------------------

@tool
def böl(a: float, b: float) -> str:
    """İki ədədi bir-birinə bölür."""
    try:
        nəticə = a / b
        return f"Nəticə: {nəticə}"
    except ZeroDivisionError:
        return "Xəta: Sıfıra bölmək olmaz. Zəhmət olmasa başqa ədəd ver."


# ---------------------------------------------------------------------------
# 6. Tool-ları bir yerə toplamaq (Toolkit)
# ---------------------------------------------------------------------------

@tool
def email_göndər(alıcı: str, mətn: str) -> str:
    """Verilən alıcıya email göndərir."""
    return f"{alıcı} ünvanına email göndərildi: {mətn}"


@tool
def email_oxu(qutu: str) -> str:
    """Verilən qutudakı emailləri oxuyur."""
    return f"{qutu} qutusunda 3 yeni email var."


email_toolkit = [email_göndər, email_oxu]


def main() -> None:
    print("=== 2. Sadə tool ===")
    print("ad:", hərfləri_say.name)
    print("təsvir:", hərfləri_say.description)
    print('invoke({"mətn": "Salam"}):', hərfləri_say.invoke({"mətn": "Salam"}))
    print()

    print("=== 3. Yaxşı təsvir ===")
    print("ad:", valyuta_çevir.name)
    print("təsvir:", valyuta_çevir.description)
    print('invoke({"məbləğ": 100.0}):', valyuta_çevir.invoke({"məbləğ": 100.0}))
    print()

    print("=== 4. Pydantic schema ===")
    print('invoke({"şəhər": "Bakı"}):', havanı_yoxla.invoke({"şəhər": "Bakı"}))
    print()

    print("=== 5. Xəta idarəetməsi ===")
    print('böl({"a": 10, "b": 2}):', böl.invoke({"a": 10, "b": 2}))
    print('böl({"a": 10, "b": 0}):', böl.invoke({"a": 10, "b": 0}))
    print()

    print("=== 6. Toolkit ===")
    for t in email_toolkit:
        print(f"Tool adı: {t.name} — Təsvir: {t.description}")


if __name__ == "__main__":
    main()
