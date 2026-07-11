import re
import streamlit as st
from core.config import get_report_date_range, get_report_year
from core.db import get_connection
from core.intent import parse_question
from reports.cards import build_category_card, build_product_360_card, build_product_yearly_card, render_card
from reports.category_profit import run_category_profit
from reports.daily_profit import render_daily_profit, run_daily_profit
from reports.period_profit import run_period_profit
from reports.product_360 import run_product_360
from reports.product_search import find_product_cached, fuzzy_find
from reports.product_yearly import run_product_yearly
from reports.stock_inactivity import render_stock_inactivity, run_stock_inactivity
from reports.supplier_profit import render_supplier_profit, run_supplier_profit

APP_VERSION='v3.12.1_app_syntax_fix'
st.set_page_config(page_title='Ertan Market Veri Asistanı', page_icon='📊', layout='wide', initial_sidebar_state='collapsed')
st.markdown('<style>#MainMenu, footer{visibility:hidden}.block-container{max-width:96vw!important;padding-top:2rem!important;padding-left:1.5rem!important;padding-right:1.5rem!important;padding-bottom:6rem!important}[data-testid="stMetricValue"]{font-size:1.08rem}[data-testid="stMetricLabel"]{font-size:.72rem}[data-testid="stDataFrame"]{width:100%!important}</style>', unsafe_allow_html=True)
if st.session_state.get('_app_version')!=APP_VERSION:
    st.session_state.clear(); st.session_state['_app_version']=APP_VERSION
st.session_state.setdefault('history',[]); st.session_state.setdefault('pending_picker',None)

def add_user(t): st.session_state.history.append({'role':'user','text':t})
def add_text(t,level='info'): st.session_state.history.append({'role':'assistant','text':t,'level':level})
def add_card(c): st.session_state.history.append({'role':'assistant','card':c})
def add_profit(df,label): st.session_state.history.append({'role':'assistant','profit_report':{'df':df,'label':label}})
def add_stock(df,days): st.session_state.history.append({'role':'assistant','stock_report':{'df':df,'days':days}})
def add_supplier(df,label): st.session_state.history.append({'role':'assistant','supplier_report':{'df':df,'label':label}})

def is_stock_q(q):
    s=q.lower(); return ('satmayan' in s or 'satılmayan' in s or 'satilmayan' in s or 'hareketsiz' in s or 'stokta çok duran' in s or 'stokta cok duran' in s)
def days_from_q(q):
    m=re.search(r'son\s+(\d{1,3})\s*g[uü]n', q.lower());
    if m: return int(m.group(1))
    if '60' in q: return 60
    if '90' in q or 'çok duran' in q.lower() or 'cok duran' in q.lower(): return 90
    return 30
def is_supplier_q(q):
    s=q.lower(); return ('tedarikçi' in s or 'tedarikci' in s or 'hangi tedarikçiden' in s or 'hangi tedarikciden' in s or 'yüksek ciro' in s or 'yuksek ciro' in s)

def pdf_profit(df,label):
    try:
        from reports.pdf_export import build_profit_pdf, safe_filename
        st.download_button('📄 PDF raporu indir', build_profit_pdf(df,label), safe_filename(label), 'application/pdf', type='primary', width='stretch')
    except Exception as e: st.error(f'PDF oluşturulamadı: {e}')
def pdf_stock(df,days):
    try:
        from reports.simple_pdf import build_stock_pdf, safe_filename
        label=f'Son {days} gündür satmayan ürünler'; st.download_button('📄 Satmayan stok PDF indir', build_stock_pdf(df,label), safe_filename(label,'ertan_satmayan_stok'), 'application/pdf', type='primary', width='stretch')
    except Exception as e: st.error(f'PDF oluşturulamadı: {e}')
def pdf_supplier(df,label):
    try:
        from reports.simple_pdf import build_supplier_pdf, safe_filename
        st.download_button('📄 Tedarikçi PDF indir', build_supplier_pdf(df,label), safe_filename(label,'ertan_tedarikci_karlilik'), 'application/pdf', type='primary', width='stretch')
    except Exception as e: st.error(f'PDF oluşturulamadı: {e}')

def run_report_for_barcode(conn, rt, barkod):
    if rt=='product_yearly':
        df=run_product_yearly(conn,barkod); add_card(build_product_yearly_card(df)) if not df.empty else add_text('Bu ürün için yıllık veri bulunamadı.','warning')
    else:
        df=run_product_360(conn,barkod); add_card(build_product_360_card(df)) if not df.empty else add_text('Bu ürün için rapor verisi bulunamadı.','warning')

def process_question(q):
    conn=None
    try:
        intent=parse_question(q); conn=get_connection()
        if is_stock_q(q):
            days=days_from_q(q); add_stock(run_stock_inactivity(conn,days), days); return
        if is_supplier_q(q):
            if getattr(intent,'start_date',None) and getattr(intent,'end_date',None): start,end,label=intent.start_date,intent.end_date,intent.report_label
            else: start,end=get_report_date_range(); label=f'{get_report_year()} yılı'
            df=run_supplier_profit(conn,start,end); add_supplier(df,label) if not df.empty else add_text(f'{label} için tedarikçi kârlılık verisi bulunamadı.','warning'); return
        if intent.report_type=='period_profit':
            df=run_period_profit(conn,intent.start_date,intent.end_date); add_profit(df,intent.report_label or f'{intent.start_date} - {intent.end_date}') if not df.empty else add_text('Bu dönem için satış verisi bulunamadı.','warning'); return
        if intent.report_type=='daily_profit':
            df=run_daily_profit(conn,intent.report_date); add_profit(df,intent.report_date) if not df.empty else add_text(f'{intent.report_date} tarihi için satış verisi bulunamadı.','warning'); return
        if intent.report_type=='category_profit':
            if not intent.category: add_text('Kategori anlayamadım.','warning'); return
            df=run_category_profit(conn,intent.category,limit=50); add_card(build_category_card(df,intent.category)) if not df.empty else add_text(f'{intent.category} kategorisi için sonuç bulunamadı.','warning'); return
        products=find_product_cached(conn, barcode=intent.barcode, product_text=intent.product_text)
        if products.empty and intent.product_text: products=fuzzy_find(conn,intent.product_text)
        if products.empty: add_text('Ürün bulamadım. Barkodla dener misin?','warning'); return
        if len(products)>1: st.session_state.pending_picker={'report_type':intent.report_type,'products':products}; return
        run_report_for_barcode(conn,intent.report_type,products.iloc[0]['Barkod'])
    except Exception as e: add_text(f'Bir hata oluştu: `{e}`','warning')
    finally:
        if conn is not None: conn.close()

st.title('📊 Ertan Market Veri Asistanı'); st.caption(f'Rapor yılı: {get_report_year()} · Sohbet eder gibi sor, net cevap al.')
with st.sidebar:
    st.header('Hızlı Sorular')
    examples=['2026 haziran ayı net karlılık','2026 haziran tedarikçi karlılık raporu','Hangi tedarikçi yüksek ciro ama düşük kâr getiriyor?','Son 30 gündür satmayan ürünler','Son 60 gündür satmayan ürünler','Son 90 gündür satmayan ürünler','Stokta çok duran ama satmayan ürünler','08.07.2026 net kârlılık','5099873090183 analiz et']
    ex=st.radio('Örnek seç:',examples,index=0)
    if st.button('Örneği çalıştır',width='stretch'): st.session_state['pending_question']=ex
    st.divider()
    if st.button('🧹 Sohbeti temizle',width='stretch'): st.session_state.history=[]; st.session_state.pending_picker=None; st.rerun()
for entry in st.session_state.history:
    with st.chat_message(entry['role']):
        if 'profit_report' in entry:
            r = entry['profit_report']
            pdf_profit(r['df'], r['label'])
            render_daily_profit(r['df'], r['label'], show_summary=True)

        elif 'stock_report' in entry:
            r = entry['stock_report']
            pdf_stock(r['df'], r['days'])
            render_stock_inactivity(r['df'], r['days'])

        elif 'supplier_report' in entry:
            r = entry['supplier_report']
            pdf_supplier(r['df'], r['label'])
            render_supplier_profit(r['df'], r['label'])

        elif 'card' in entry:
            render_card(entry['card'])

        else:
            if entry.get('level') == 'warning':
                st.warning(entry['text'])
            else:
                st.markdown(entry['text'])
picker=st.session_state.pending_picker
if picker is not None:
    with st.chat_message('assistant'):
        st.markdown('**Birden fazla ürün bulundu.** Analiz edilecek ürünü seç:')
        products=picker['products']; opts=[f"{r.Barkod} | {r.UrunAdi} | {(r.AnaKategori or '')} / {(r.AltKategori or '')}" for r in products.itertuples()]
        sel=st.selectbox('Ürün',opts,label_visibility='collapsed')
        if st.button('Analiz et',type='primary'):
            barkod=products.iloc[opts.index(sel)]['Barkod']; st.session_state.pending_picker=None
            conn=None
            try: conn=get_connection(); run_report_for_barcode(conn,picker['report_type'],barkod)
            except Exception as e: add_text(f'Bir hata oluştu: `{e}`','warning')
            finally:
                if conn is not None: conn.close()
            st.rerun()
q=st.chat_input('Örnek: Son 30 gündür satmayan ürünler')
if 'pending_question' in st.session_state: q=st.session_state.pop('pending_question')
if q: add_user(q); st.session_state.pending_picker=None; process_question(q); st.rerun()
if not st.session_state.history and picker is None: st.info('Başlamak için stok, tedarikçi, tarih, ay, barkod veya ürün sorusu yaz.')
