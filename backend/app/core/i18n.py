from typing import Any


def normalize_lang(lang: str | None) -> str:
    if not lang:
        return "en"
    return "ar" if str(lang).lower().startswith("ar") else "en"


def response_payload(data: Any, en: str, ar: str, lang: str | None = "en") -> dict[str, Any]:
    selected = normalize_lang(lang)
    return {
        "ok": True,
        "message": ar if selected == "ar" else en,
        "messages": {"en": en, "ar": ar},
        "lang": selected,
        "data": data,
    }


def error_payload(en: str, ar: str, lang: str | None = "en") -> dict[str, Any]:
    selected = normalize_lang(lang)
    return {
        "ok": False,
        "message": ar if selected == "ar" else en,
        "messages": {"en": en, "ar": ar},
        "lang": selected,
    }
