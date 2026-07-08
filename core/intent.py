import re
from dataclasses import dataclass

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

def extract_barcode(question: str) -> str | None:
    match = re.search(r"\b\d{8,14}\b", question)
    return match.group(0) if match else None

def extract_category(question: str) -> str | None:
    q = question.lower()
    for alias, category in CATEGORY_ALIASES.items():
        if alias in q:
            return category
    return None

def detect_report_type(question: str) -> str:
    q = question.lower()

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
    report_type = detect_report_type(question)
    product_text = None if barcode or report_type == "category_profit" else clean_product_text(question)

    return Intent(
        report_type=report_type,
        barcode=barcode,
        product_text=product_text if product_text else None,
        category=category,
        raw_question=question,
    )
