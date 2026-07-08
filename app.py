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
from reports.product_360 import run_product_360
from reports.product_search import find_product_cached, fuzzy_find
from reports.product_yearly import run_product_yearly


st.set_page_config(
    page_title="Ertan Market Veri Asistanı",
    page_icon="📊",
    layout="centered",
)

st.markdown(
    """
    <style>
    #MainMenu, footer {visibility: hidden;}
    [data-testid="stMetricValue"] {font-size: 1.15rem;}
    [data-testid="stMetricLabel"] {font-size: 0.75rem;}
    .block-container {padding-top: 2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- durum ----------
if "history" not in st.session_state:
    st.session_state.history = []  # {"role": "user"/"assistant", "text": str} veya {"role": "assistant", "card": dict}
if "pending_picker" not in st.session_state:
    st.session_state.pending_picker = None  # {"intent_report": str, "products": df}


def add_user(text: str):
    st.session_state.history.append({"role": "user", "text": text})


def add_text(text: str, level: str = "info"):
    st.session_state.history.append({"role": "assistant", "text": text, "level": level})


def add_card(card: dict):
    st.session_state.history.append({"role": "assistant", "card": card})


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

        # LIKE bulamadiysa bulanik arama dene
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
        if "card" in entry:
            render_card(entry["card"])
        else:
            if entry.get("level") == "warning":
                st.warning(entry["text"])
            else:
                st.markdown(entry["text"])

# ---------- urun secici (bekleyen) ----------
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
question = st.chat_input("Örnek: Chivas 12 son yıllar alış satış")

if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    add_user(question)
    st.session_state.pending_picker = None
    process_question(question)
    st.rerun()

if not st.session_state.history and picker is None:
    st.info("Başlamak için barkod, ürün adı veya kategori yaz. Yazım hatası dert değil — *'jack danials'* bile bulunur. 😉")
