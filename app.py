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
from reports.product_360 import run_product_360
from reports.product_search import find_product_cached, fuzzy_find
from reports.product_yearly import run_product_yearly


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
        max-width: 95vw !important;
        padding-top: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-bottom: 6rem !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.15rem;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.75rem;
    }

    [data-testid="stDataFrame"] {
        width: 100% !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.75rem;
    }

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


def add_daily_report(df, report_date: str):
    # Günlük raporu kart/expander içine gömmüyoruz.
    # Sekmeler doğrudan görünür olsun diye ayrı history tipi.
    st.session_state.history.append(
        {
            "role": "assistant",
            "daily_report": {
                "df": df,
                "report_date": report_date,
            },
        }
    )


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

        if intent.report_type == "daily_profit":
            if not intent.report_date:
                add_text("Tarih anlayamadım. Örnek: *08.07.2026 net kârlılık*", "warning")
                return
            df = run_daily_profit(conn, intent.report_date)
            if df.empty:
                add_text(f"{intent.report_date} tarihi için satış verisi bulunamadı.", "warning")
                return
            add_daily_report(df, intent.report_date)
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
    st.caption("Kâr referansı: KDV hariç satış − KDV hariç alış maliyeti.")


# ---------- gecmisi ciz ----------
for entry in st.session_state.history:
    with st.chat_message(entry["role"]):
        if "daily_report" in entry:
            st.markdown("**🧾 Günlük Satış ve Maliyet Sağlık Kontrolü**")
            render_daily_profit(
                entry["daily_report"]["df"],
                entry["daily_report"]["report_date"],
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
question = st.chat_input("Örnek: 08.07.2026 net kârlılık")

if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    add_user(question)
    st.session_state.pending_picker = None
    process_question(question)
    st.rerun()

if not st.session_state.history and picker is None:
    st.info("Başlamak için tarih, barkod, ürün adı veya kategori yaz. Örnek: *08.07.2026 net kârlılık*")
