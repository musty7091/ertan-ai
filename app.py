import streamlit as st

from core.db import get_connection
from core.intent import parse_question
from reports.category_profit import render_category_profit, run_category_profit
from reports.product_360 import render_product_360, run_product_360
from reports.product_search import find_product
from reports.product_yearly import render_product_yearly, run_product_yearly


st.set_page_config(
    page_title="Ertan Market Veri Asistanı",
    page_icon="📊",
    layout="wide",
)


def render_product_picker(products):
    options = [
        f"{row.Barkod} | {row.UrunAdi} | {row.AnaKategori or ''} / {row.AltKategori or ''}"
        for row in products.itertuples()
    ]

    selected = st.selectbox("Birden fazla ürün bulundu. Analiz edilecek ürünü seç:", options)
    selected_index = options.index(selected)
    return products.iloc[selected_index]["Barkod"]


def run_product_report(conn, report_type: str, barkod: str):
    if report_type == "product_yearly":
        df = run_product_yearly(conn, barkod)
        render_product_yearly(df)
        return

    df = run_product_360(conn, barkod)
    render_product_360(df)


def run_assistant(question: str):
    conn = None
    try:
        intent = parse_question(question)
        conn = get_connection()

        if intent.report_type == "category_profit":
            if not intent.category:
                st.warning("Kategori anlayamadım. Örnek: Whiskey kategorisinde en kârlı ürünler")
                return

            st.caption(f"Rapor tipi: 2026 kategori kârlılık | Kategori: {intent.category}")
            df = run_category_profit(conn, intent.category, limit=50)
            render_category_profit(df, intent.category)
            return

        products = find_product(
            conn,
            barcode=intent.barcode,
            product_text=intent.product_text,
        )

        if products.empty:
            st.warning("Bu sorudan ürün/barkod bulamadım. Barkodla dene: 5099873090183 analiz et")
            return

        if len(products) > 1:
            selected_barkod = render_product_picker(products)
        else:
            selected_barkod = products.iloc[0]["Barkod"]

        if intent.report_type == "product_yearly":
            st.caption("Rapor tipi: Son yıllar alış-satış")
        else:
            st.caption("Rapor tipi: 2026 Ürün 360")

        run_product_report(conn, intent.report_type, selected_barkod)

    except Exception as exc:
        st.error("Bir hata oluştu.")
        st.code(str(exc))
    finally:
        if conn is not None:
            conn.close()


st.title("📊 Ertan Market Veri Asistanı")
st.write("Sohbet eder gibi ürün, kategori ve kârlılık soruları sor.")

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
    st.caption("Not: Kâr hesabında ana referans KDV hariç satış - KDV hariç alış maliyetidir.")

question = st.chat_input("Örnek: Chivas 12 son yıllar alış satış")

if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        run_assistant(question)
else:
    st.info(
        "Başlamak için barkod, ürün adı veya kategori yaz. Örnek: `080432400395 son yıllar alış satış`"
    )
