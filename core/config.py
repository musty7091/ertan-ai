import os
from datetime import date

from dotenv import load_dotenv

load_dotenv()


def get_report_year() -> int:
    """Aktif rapor yılı. .env içinde REPORT_YEAR yoksa içinde bulunulan yıl kullanılır."""
    raw = os.getenv("REPORT_YEAR", "").strip()
    if raw.isdigit():
        return int(raw)
    return date.today().year


def get_report_date_range() -> tuple[str, str]:
    """Rapor yılının [başlangıç, bitiş) tarih aralığı (bitiş hariç)."""
    year = get_report_year()
    return f"{year}-01-01", f"{year + 1}-01-01"


def get_excluded_sale_header_ind() -> int:
    """
    Satış entegrasyon başlığında rapor dışı tutulan kayıt.
    Varsayılan 166576: hatalı/mükerrer entegrasyon başlığı olduğu için
    tüm satış raporlarından dışlanır. Gerekirse .env içinde
    EXCLUDED_SALE_HEADER_IND ile değiştirilebilir.
    """
    raw = os.getenv("EXCLUDED_SALE_HEADER_IND", "166576").strip()
    if raw.lstrip("-").isdigit():
        return int(raw)
    return -1
