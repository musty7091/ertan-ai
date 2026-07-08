# -*- coding: utf-8 -*-
"""Turkce metin normalizasyonu: buyuk/kucuk harf ve Turkce karakter
farklarini yok ederek bulanik eslestirmeyi guclendirir."""

_MAP = str.maketrans({
    "ı": "i", "İ": "i", "I": "i",
    "ş": "s", "Ş": "s",
    "ç": "c", "Ç": "c",
    "ğ": "g", "Ğ": "g",
    "ü": "u", "Ü": "u",
    "ö": "o", "Ö": "o",
})


def normalize(text: str) -> str:
    if text is None:
        return ""
    return str(text).translate(_MAP).lower().strip()
