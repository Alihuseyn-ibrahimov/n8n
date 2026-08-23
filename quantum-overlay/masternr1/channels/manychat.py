"""ManyChat External Request / Dynamic Content köməkçiləri.

Meta App Review (instagram_manage_messages Advanced Access) keçilənə qədər
Instagram DM-lər ManyChat üzərindən gəlir. ManyChat-in gövdə formatı axın
quraşdırmasından asılıdır — bir neçə ümumi variantı qəbul edirik.
"""

from __future__ import annotations


def extract_fields(payload: dict) -> tuple[str, str, str]:
    """(subscriber_id, text, display_name) çıxarır.

    ManyChat Custom User Field / External Request gövdələri fərqli açarlar
    işlədir: `subscriber_id`, `last_input_text`, iç-içə `subscriber.id` və s.
    """
    subscriber = payload.get("subscriber") if isinstance(payload.get("subscriber"), dict) else {}
    subscriber_id = str(
        payload.get("subscriber_id")
        or payload.get("id")
        or payload.get("user_id")
        or subscriber.get("id")
        or ""
    ).strip()

    text = str(
        payload.get("text")
        or payload.get("last_input_text")
        or payload.get("last_text_input")
        or payload.get("message")
        or payload.get("last_input")
        or ""
    ).strip()

    first = str(payload.get("first_name") or subscriber.get("first_name") or "").strip()
    last = str(payload.get("last_name") or subscriber.get("last_name") or "").strip()
    name = " ".join(part for part in (first, last) if part)
    return subscriber_id, text, name


def build_response(reply: str) -> dict:
    """Həm sadə `reply` sahəsi, həm ManyChat Dynamic Content v2 formatı.

    ManyChat axını iki cür qurula bilər:
    - External Request → `{{response.reply}}` custom field-ə yaz, sonra Send Message
    - Dynamic Content: birbaşa `content.messages` oxunur
    """
    messages = [{"type": "text", "text": reply}] if reply else []
    return {
        "reply": reply,
        "version": "v2",
        "content": {"messages": messages},
    }
