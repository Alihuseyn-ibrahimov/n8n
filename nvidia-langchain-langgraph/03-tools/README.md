# Example Code (3) — LangChain Tools

**Kurs:** LangChain və LangGraph — Vəziyyətli Qraflar, Yoxlama Nöqtələri və NVIDIA İnteqrasiyası

Bu qovluq dərsin tool mövzusunu kodla göstərir. Tool LLM-ə xarici dünya ilə əlaqə imkanı verir: hava, hesab, email və s.

## Nə öyrənirik

1. Tool nədir və niyə lazımdır
2. `@tool` dekoratoru ilə sadə tool
3. Təsvirin (description / docstring) modeli necə yönləndirdiyi
4. Pydantic schema ilə giriş yoxlaması
5. `try/except` ilə xəta idarəetməsi
6. Əlaqəli tool-ları toolkit (siyahı) kimi yığmaq

## Quraşdırma

```bash
cd nvidia-langchain-langgraph/03-tools
pip install -r requirements.txt
```

## İşə salmaq

Dərs nümunələri:

```bash
python3 example_03_tools.py
```

Ev tapşırığı:

```bash
python3 ev_tapshirigi.py
```

Gözlənilən ev tapşırığı nəticəsi:

```
36.0
80.0
Xəta: Endirim 100 faizdən çox ola bilməz.
vergi_hesabla
endirim_tətbiq_et
```

## Fayllar

| Fayl | Məzmun |
| --- | --- |
| `example_03_tools.py` | Dərsin bütün nümunələri: sadə tool, təsvir, Pydantic, xəta, toolkit |
| `ev_tapshirigi.py` | `vergi_hesabla` + `endirim_tətbiq_et` və `hesab_toolkit` |
| `requirements.txt` | `langchain-core` və `pydantic` |
