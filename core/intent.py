import re
from dataclasses import dataclass
from datetime import date, timedelta


CATEGORY_ALIASES = {
    "whiskey": "WHISKEY",
    "viski": "WHISKEY",
    "whisky": "WHISKEY",
    "rakı": "RAKI",
    "raki": "RAKI",
    "likör": "LIKOR",
    "likor": "LIKOR",
    "vodka": "VODKA",
    "votka": "VODKA",
    "gin": "GIN",
    "cin": "GIN",
    "rom": "ROM",
    "tekila": "TEKILA",
    "tequila": "TEKILA",
    "şarap": "SARAP",
    "sarap": "SARAP",
    "bira": "BIRA",
}


@dataclass
class Intent:
    report_type: str
    barcode: str | None
    product_text: str | None
    category: str | None
    raw_question: str
    report_date: str | None = None


def extract_barcode(question: str) -> str | None:
    match = re.search(r"\b\d{8,14}\b", question)
    return match.group(0) if match else None


def extract_category(question: str) -> str | None:
    q = question.lower()
    for alias, category in CATEGORY_ALIASES.items():
        if alias in q:
            return category
    return None


def extract_report_date(question: str) -> str | None:
    q = question.lower().strip()

    if "bugün" in q or "bugun" in q:
        return date.today().isoformat()

    if "dün" in q or "dun" in q:
        return (date.today() - timedelta(days=1)).isoformat()

    iso = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", question)
    if iso:
        year, month, day = map(int, iso.groups())
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None

    dotted = re.search(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b", question)
    if dotted:
        day, month, year = map(int, dotted.groups())
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None

    months = {
        "ocak": 1,
        "şubat": 2,
        "subat": 2,
        "mart": 3,
        "nisan": 4,
        "mayıs": 5,
        "mayis": 5,
        "haziran": 6,
        "temmuz": 7,
        "ağustos": 8,
        "agustos": 8,
        "eylül": 9,
        "eylul": 9,
        "ekim": 10,
        "kasım": 11,
        "kasim": 11,
        "aralık": 12,
        "aralik": 12,
    }

    text_date = re.search(
        r"\b(\d{1,2})\s+(" + "|".join(months.keys()) + r")\s+(\d{4})\b",
        q,
    )
    if text_date:
        day = int(text_date.group(1))
        month = months[text_date.group(2)]
        year = int(text_date.group(3))
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None

    return None


def detect_report_type(question: str) -> str:
    q = question.lower()
    report_date = extract_report_date(question)

    daily_keywords = [
        "net kar",
        "net kâr",
        "karlılık",
        "karliligi",
        "kârlılık",
        "kârlılığı",
        "karlılığı",
        "günlük kar",
        "gunluk kar",
        "günlük kâr",
        "gunluk kâr",
        "tüm satış",
        "tum satis",
        "tüm satis",
        "günün satışı",
        "gunun satisi",
    ]

    if report_date and any(keyword in q for keyword in daily_keywords):
        return "daily_profit"

    if report_date and ("satış" in q or "satis" in q or "ciro" in q):
        return "daily_profit"

    if ("bugün" in q or "bugun" in q or "dün" in q or "dun" in q) and (
        "kar" in q or "kâr" in q or "karl" in q or "satış" in q or "satis" in q
    ):
        return "daily_profit"

    yearly_keywords = [
        "son yıl", "son yıllar", "son yillar", "son yıllardaki",
        "yıllık", "yillik", "yıllar", "yillar", "geçmiş", "gecmis",
        "trend", "alış satış", "alis satis", "alış-satış", "alis-satis",
    ]

    category_keywords = [
        "kategori", "kategorisinde", "en karlı", "en karli", "en kârlı",
        "en çok kâr", "en cok kar", "en çok satan", "en cok satan",
        "kâr bırakan", "kar birakan",
    ]

    if any(keyword in q for keyword in yearly_keywords):
        return "product_yearly"

    if any(keyword in q for keyword in category_keywords) or extract_category(question):
        return "category_profit"

    return "product_360"


def clean_product_text(question: str) -> str:
    text = question.strip()

    patterns = [
        r"\b\d{8,14}\b", r"\banaliz et\b", r"\banalizi\b", r"\banaliz\b",
        r"\bgöster\b", r"\bgoster\b", r"\bson yıllar\b", r"\bson yillar\b",
        r"\bson yıllardaki\b", r"\byıllık\b", r"\byillik\b", r"\byıllar\b",
        r"\byillar\b", r"\balış satış\b", r"\balis satis\b", r"\balış-satış\b",
        r"\balis-satis\b", r"\btrend\b", r"\bgeçmiş\b", r"\bgecmis\b",
        r"\bkarlılık\b", r"\bkarlilik\b", r"\bkârlılık\b", r"\bkategorisinde\b",
        r"\bkategori\b", r"\ben çok satan\b", r"\ben cok satan\b",
        r"\ben karlı\b", r"\ben karli\b", r"\ben kârlı\b",
        r"\b\d{4}-\d{1,2}-\d{1,2}\b",
        r"\b\d{1,2}[./]\d{1,2}[./]\d{4}\b",
    ]

    for pattern in patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    for alias in CATEGORY_ALIASES:
        text = re.sub(rf"\b{re.escape(alias)}\b", " ", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_question(question: str) -> Intent:
    barcode = extract_barcode(question)
    category = extract_category(question)
    report_date = extract_report_date(question)
    report_type = detect_report_type(question)
    product_text = None if barcode or report_type in ("category_profit", "daily_profit") else clean_product_text(question)

    return Intent(
        report_type=report_type,
        barcode=barcode,
        product_text=product_text if product_text else None,
        category=category,
        raw_question=question,
        report_date=report_date,
    )
