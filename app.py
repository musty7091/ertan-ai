import streamlit as st

from core.config import get_report_year
from core.db import get_connection
from core.intent import parse_question
from reports.cards import (
    build_category_card,
    build_product_360_card,
    build_product_yearly_card,
    render_card,
)
from reports.category_profit import run_category_profit
from reports.daily_profit import render_daily_profit, run_daily_profit
from reports.period_profit import run_period_profit
from reports.product_360 import run_product_360
from reports.product_search import find_product_cached, fuzzy_find
from reports.product_yearly import run_product_yearly


APP_VERSION = "v3.11_pdf_export"


st.set_page_config(
    page_title="Ertan Market Veri Asistanı",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    #MainMenu, footer {visibility: hidden;}

    .block-container {
        max-width: 96vw !important;
        padding-top: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        padding-bottom: 6rem !important;
    }

    [data-testid="stMetricValue"] { font-size: 1.08rem; }
    [data-testid="stMetricLabel"] { font-size: 0.72rem; }
    [data-testid="stDataFrame"] { width: 100% !important; }

    div[data-testid="stVerticalBlock"] { gap: 0.75rem; }

    @media (max-width: 900px) {
        .block-container {
            max-width: 100vw !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- durum ----------
if st.session_state.get("_app_version") != APP_VERSION:
    st.session_state.clear()
    st.session_state["_app_version"] = APP_VERSION

if "history" not in st.session_state:
    st.session_state.history = []
if "pending_picker" not in st.session_state:
    st.session_state.pending_picker = None


def add_user(text: str):
    st.session_state.history.append({"role": "user", "text": text})


def add_text(text: str, level: str = "info"):
    st.session_state.history.append({"role": "assistant", "text": text, "level": level})


def add_card(card: dict):
    st.session_state.history.append({"role": "assistant", "card": card})


def add_profit_report(df, report_label: str):
    st.session_state.history.append(
        {
            "role": "assistant",
            "profit_report": {
                "df": df,
                "report_label": report_label,
            },
        }
    )


def render_pdf_download(df, report_label: str):
    try:
        from reports.pdf_export import build_profit_pdf, safe_filename
    except ModuleNotFoundError:
        st.error(
            "PDF oluşturmak için reportlab paketi gerekli. "
            "PowerShell'de şu komutu çalıştır: pip install reportlab"
        )
        return
    except Exception as exc:
        st.error(f"PDF modülü yüklenemedi: {exc}")
        return

    try:
        pdf_bytes = build_profit_pdf(df, report_label)
        st.download_button(
            label="📄 PDF raporu indir",
            data=pdf_bytes,
            file_name=safe_filename(report_label),
            mime="application/pdf",
            type="primary",
            width="stretch",
        )
    except Exception as exc:
        st.error(f"PDF oluşturulamadı: {exc}")


# ---------- rapor calistirma ----------
def run_report_for_barcode(conn, report_type: str, barkod: str):
    if report_type == "product_yearly":
        df = run_product_yearly(conn, barkod)
        if df.empty:
            add_text("Bu ürün için yıllık veri bulunamadı.", "warning")
            return
        add_card(build_product_yearly_card(df))
    else:
        df = run_product_360(conn, barkod)
        if df.empty:
            add_text("Bu ürün için rapor verisi bulunamadı.", "warning")
            return
        add_card(build_product_360_card(df))


def process_question(question: str):
    conn = None
    try:
        intent = parse_question(question)
        conn = get_connection()

        if intent.report_type == "period_profit":
            if not intent.start_date or not intent.end_date:
                add_text(
                    "Tarih aralığını anlayamadım. Örnek: *2026 Haziran ayı net karlılık* "
                    "veya *01.06.2026 - 30.06.2026 net karlılık*",
                    "warning",
                )
                return
            df = run_period_profit(conn, intent.start_date, intent.end_date)
            if df.empty:
                add_text(f"{intent.report_label or intent.start_date} için satış verisi bulunamadı.", "warning")
                return
            add_profit_report(df, intent.report_label or f"{intent.start_date} - {intent.end_date}")
            return

        if intent.report_type == "daily_profit":
            if not intent.report_date:
                add_text("Tarih anlayamadım. Örnek: *08.07.2026 net kârlılık*", "warning")
                return
            df = run_daily_profit(conn, intent.report_date)
            if df.empty:
                add_text(f"{intent.report_date} tarihi için satış verisi bulunamadı.", "warning")
                return
            add_profit_report(df, intent.report_date)
            return

        if intent.report_type == "category_profit":
            if not intent.category:
                add_text("Kategori anlayamadım. Örnek: *Whiskey kategorisinde en kârlı ürünler*", "warning")
                return
            df = run_category_profit(conn, intent.category, limit=50)
            if df.empty:
                add_text(f"{intent.category} kategorisi için sonuç bulunamadı.", "warning")
                return
            add_card(build_category_card(df, intent.category))
            return

        products = find_product_cached(
            conn,
            barcode=intent.barcode,
            product_text=intent.product_text,
        )

        fuzzy_used = False
        if products.empty and intent.product_text:
            products = fuzzy_find(conn, intent.product_text)
            fuzzy_used = not products.empty

        if products.empty:
            add_text("Ürün bulamadım. Barkodla dener misin? Örnek: *5099873090183 analiz et*", "warning")
            return

        if len(products) > 1:
            if fuzzy_used:
                add_text("Tam eşleşme yok ama benzer ürünler buldum. Aşağıdan seç:")
            st.session_state.pending_picker = {
                "report_type": intent.report_type,
                "products": products,
            }
            return

        run_report_for_barcode(conn, intent.report_type, products.iloc[0]["Barkod"])

    except Exception as exc:
        add_text(f"Bir hata oluştu: `{exc}`", "warning")
    finally:
        if conn is not None:
            conn.close()


# ---------- baslik + kenar cubugu ----------
st.title("📊 Ertan Market Veri Asistanı")
st.caption(f"Rapor yılı: {get_report_year()} · Sohbet eder gibi sor, net cevap al.")

with st.sidebar:
    st.header("Hızlı Sorular")
    examples = [
        "2026 haziran ayı net karlılık",
        "01.06.2026 - 30.06.2026 net karlılık",
        "08.07.2026 net kârlılık",
        "2026-07-08 günlük kâr",
        "5099873090183 analiz et",
        "Jack Daniels 1LT analiz et",
        "080432400395 son yıllar alış satış",
        "Chivas 12 son yıllar",
        "Whiskey kategorisinde en kârlı ürünler",
        "Rakı kategorisinde en çok satanlar",
    ]
    selected_example = st.radio("Örnek seç:", examples, index=0)
    if st.button("Örneği çalıştır", width="stretch"):
        st.session_state["pending_question"] = selected_example

    st.divider()
    if st.button("🧹 Sohbeti temizle", width="stretch"):
        st.session_state.history = []
        st.session_state.pending_picker = None
        st.rerun()
    st.caption("Kâr referansı: KDV hariç satış − stok kartı bazlı maliyet.")


# ---------- gecmisi ciz ----------
for entry in st.session_state.history:
    with st.chat_message(entry["role"]):
        if "profit_report" in entry:
            report = entry["profit_report"]
            render_pdf_download(report["df"], report["report_label"])
            render_daily_profit(
                report["df"],
                report["report_label"],
                show_summary=True,
            )
        elif "daily_report" in entry:
            # Eski history desteği
            report = entry["daily_report"]
            report_label = report.get("report_label") or report.get("report_date", "rapor")
            render_pdf_download(report["df"], report_label)
            render_daily_profit(
                report["df"],
                report_label,
                show_summary=True,
            )
        elif "card" in entry:
            render_card(entry["card"])
        else:
            if entry.get("level") == "warning":
                st.warning(entry["text"])
            else:
                st.markdown(entry["text"])


# ---------- urun secici ----------
picker = st.session_state.pending_picker
if picker is not None:
    with st.chat_message("assistant"):
        st.markdown("**Birden fazla ürün bulundu.** Analiz edilecek ürünü seç:")
        products = picker["products"]
        options = [
            f"{row.Barkod} | {row.UrunAdi} | {(row.AnaKategori or '')} / {(row.AltKategori or '')}"
            for row in products.itertuples()
        ]
        selected = st.selectbox("Ürün", options, label_visibility="collapsed")
        if st.button("Analiz et", type="primary"):
            barkod = products.iloc[options.index(selected)]["Barkod"]
            st.session_state.pending_picker = None
            conn = None
            try:
                conn = get_connection()
                run_report_for_barcode(conn, picker["report_type"], barkod)
            except Exception as exc:
                add_text(f"Bir hata oluştu: `{exc}`", "warning")
            finally:
                if conn is not None:
                    conn.close()
            st.rerun()


# ---------- giris ----------
question = st.chat_input("Örnek: 2026 Haziran ayı net karlılık")

if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    add_user(question)
    st.session_state.pending_picker = None
    process_question(question)
    st.rerun()

if not st.session_state.history and picker is None:
    st.info("Başlamak için tarih, tarih aralığı, ay, barkod, ürün adı veya kategori yaz. Örnek: *2026 Haziran ayı net karlılık*")
