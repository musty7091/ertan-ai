import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta


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

MONTHS = {
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

MONTH_NAMES_TR = {
    1: "Ocak",
    2: "Şubat",
    3: "Mart",
    4: "Nisan",
    5: "Mayıs",
    6: "Haziran",
    7: "Temmuz",
    8: "Ağustos",
    9: "Eylül",
    10: "Ekim",
    11: "Kasım",
    12: "Aralık",
}


@dataclass
class Intent:
    report_type: str
    barcode: str | None
    product_text: str | None
    category: str | None
    raw_question: str
    report_date: str | None = None
    start_date: str | None = None
    end_date: str | None = None  # exclusive end date
    report_label: str | None = None


def _month_end_exclusive(year: int, month: int) -> date:
    if month == 12:
        return date(year + 1, 1, 1)
    return date(year, month + 1, 1)


def _parse_date_token(token: str) -> date | None:
    token = token.strip()

    iso = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", token)
    if iso:
        y, m, d = map(int, iso.groups())
        try:
            return date(y, m, d)
        except ValueError:
            return None

    dotted = re.match(r"^(\d{1,2})[./](\d{1,2})[./](\d{4})$", token)
    if dotted:
        d, m, y = map(int, dotted.groups())
        try:
            return date(y, m, d)
        except ValueError:
            return None

    return None


def _profit_keywords(question: str) -> bool:
    q = question.lower()
    keywords = [
        "net kar",
        "net kâr",
        "karlılık",
        "karlilik",
        "kârlılık",
        "kârlılığı",
        "karlılığı",
        "kar raporu",
        "kâr raporu",
        "günlük kar",
        "gunluk kar",
        "günlük kâr",
        "ciro",
        "satış",
        "satis",
    ]
    return any(k in q for k in keywords)


def extract_barcode(question: str) -> str | None:
    match = re.search(r"\b\d{8,14}\b", question)
    return match.group(0) if match else None


def extract_category(question: str) -> str | None:
    q = question.lower()
    for alias, category in CATEGORY_ALIASES.items():
        if alias in q:
            return category
    return None


def extract_month_range(question: str) -> tuple[str, str, str] | None:
    q = question.lower().strip()
    today = date.today()

    # Bu ay / geçen ay
    if "bu ay" in q:
        start = date(today.year, today.month, 1)
        end = _month_end_exclusive(today.year, today.month)
        return start.isoformat(), end.isoformat(), f"{today.year} {MONTH_NAMES_TR[today.month]}"

    if "geçen ay" in q or "gecen ay" in q:
        if today.month == 1:
            year, month = today.year - 1, 12
        else:
            year, month = today.year, today.month - 1
        start = date(year, month, 1)
        end = _month_end_exclusive(year, month)
        return start.isoformat(), end.isoformat(), f"{year} {MONTH_NAMES_TR[month]}"

    # 2026-06 net karlılık
    iso_month = re.search(r"\b(20\d{2})[-/](\d{1,2})\b", q)
    if iso_month:
        year, month = int(iso_month.group(1)), int(iso_month.group(2))
        if 1 <= month <= 12:
            start = date(year, month, 1)
            end = _month_end_exclusive(year, month)
            return start.isoformat(), end.isoformat(), f"{year} {MONTH_NAMES_TR[month]}"

    months_regex = "|".join(sorted(MONTHS.keys(), key=len, reverse=True))

    # 2026 haziran ayı
    year_first = re.search(rf"\b(20\d{{2}})\s+({months_regex})(?:\s+ayı|\s+ayi)?\b", q)
    if year_first:
        year = int(year_first.group(1))
        month = MONTHS[year_first.group(2)]
        start = date(year, month, 1)
        end = _month_end_exclusive(year, month)
        return start.isoformat(), end.isoformat(), f"{year} {MONTH_NAMES_TR[month]}"

    # haziran 2026 / haziran ayı 2026
    month_first = re.search(rf"\b({months_regex})(?:\s+ayı|\s+ayi)?\s+(20\d{{2}})\b", q)
    if month_first:
        month = MONTHS[month_first.group(1)]
        year = int(month_first.group(2))
        start = date(year, month, 1)
        end = _month_end_exclusive(year, month)
        return start.isoformat(), end.isoformat(), f"{year} {MONTH_NAMES_TR[month]}"

    # Sadece "haziran ayı" denirse mevcut yıl varsayılır.
    month_only = re.search(rf"\b({months_regex})(?:\s+ayı|\s+ayi)\b", q)
    if month_only:
        month = MONTHS[month_only.group(1)]
        year = today.year
        start = date(year, month, 1)
        end = _month_end_exclusive(year, month)
        return start.isoformat(), end.isoformat(), f"{year} {MONTH_NAMES_TR[month]}"

    return None


def extract_date_range(question: str) -> tuple[str, str, str] | None:
    # İki net tarih varsa: 01.06.2026 - 30.06.2026 veya 2026-06-01 / 2026-06-30
    tokens = re.findall(r"\b\d{4}-\d{1,2}-\d{1,2}\b|\b\d{1,2}[./]\d{1,2}[./]\d{4}\b", question)
    parsed = []
    for token in tokens:
        d = _parse_date_token(token)
        if d:
            parsed.append(d)

    if len(parsed) >= 2:
        start = min(parsed[0], parsed[1])
        end_inclusive = max(parsed[0], parsed[1])
        end_exclusive = end_inclusive + timedelta(days=1)
        label = f"{start.isoformat()} - {end_inclusive.isoformat()}"
        return start.isoformat(), end_exclusive.isoformat(), label

    return None


def extract_period_range(question: str) -> tuple[str, str, str] | None:
    # Önce explicit iki tarih, sonra ay ifadeleri.
    return extract_date_range(question) or extract_month_range(question)


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

    months_regex = "|".join(sorted(MONTHS.keys(), key=len, reverse=True))
    text_date = re.search(rf"\b(\d{{1,2}})\s+({months_regex})\s+(\d{{4}})\b", q)
    if text_date:
        day = int(text_date.group(1))
        month = MONTHS[text_date.group(2)]
        year = int(text_date.group(3))
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None

    return None


def detect_report_type(question: str) -> str:
    q = question.lower()
    period = extract_period_range(question)
    report_date = extract_report_date(question)

    if period and _profit_keywords(question):
        return "period_profit"

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
        r"\b20\d{2}[-/]\d{1,2}\b",
    ]

    for pattern in patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    for alias in CATEGORY_ALIASES:
        text = re.sub(rf"\b{re.escape(alias)}\b", " ", text, flags=re.IGNORECASE)

    for month_name in MONTHS:
        text = re.sub(rf"\b{re.escape(month_name)}\b", " ", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_question(question: str) -> Intent:
    barcode = extract_barcode(question)
    category = extract_category(question)
    report_date = extract_report_date(question)
    period = extract_period_range(question)
    report_type = detect_report_type(question)
    product_text = None if barcode or report_type in ("category_profit", "daily_profit", "period_profit") else clean_product_text(question)

    start_date = None
    end_date = None
    report_label = None
    if period:
        start_date, end_date, report_label = period

    return Intent(
        report_type=report_type,
        barcode=barcode,
        product_text=product_text if product_text else None,
        category=category,
        raw_question=question,
        report_date=report_date,
        start_date=start_date,
        end_date=end_date,
        report_label=report_label,
    )
