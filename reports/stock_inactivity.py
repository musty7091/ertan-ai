import pandas as pd
import streamlit as st
from core.db import query_df
from core.formatting import format_number, format_tl
from core.sql_loader import load_sql

NUMS=['KartKalan','KartMaliyet','KartAlisFiyati','KullanilanBirimMaliyet','TahminiStokDegeri','SatmamaGunSayisi']

def run_stock_inactivity(conn, days:int):
    return query_df(conn, load_sql('stock_inactivity.sql'), [days])

def prep(df):
    d=df.copy()
    for c in NUMS:
        if c in d.columns: d[c]=pd.to_numeric(d[c], errors='coerce')
    for c in ['Tedarikci','AnaKategori','AltKategori','Marka']:
        if c in d.columns: d[c]=d[c].fillna('YOK').replace('', 'YOK')
    return d

def fmt(df):
    x=df.copy()
    for c in ['KartMaliyet','KartAlisFiyati','KullanilanBirimMaliyet','TahminiStokDegeri']:
        if c in x.columns: x[c]=x[c].apply(format_tl)
    for c in ['KartKalan','SatmamaGunSayisi']:
        if c in x.columns: x[c]=x[c].apply(format_number)
    return x.rename(columns={'UrunAdi':'Ürün Adı','Tedarikci':'Tedarikçi','AnaKategori':'Ana Kategori','AltKategori':'Alt Kategori','KartKalan':'Stok','KartMaliyet':'Kart Maliyet','KartAlisFiyati':'Kart Alış','KullanilanBirimMaliyet':'Birim Maliyet','TahminiStokDegeri':'Tahmini Stok Değeri','SonSatisTarihi':'Son Satış Tarihi','SatmamaGunSayisi':'Satmama Günü'})

def group(d, col):
    return d.groupby(col, dropna=False).agg(UrunSayisi=('Barkod','nunique'), ToplamStok=('KartKalan','sum'), TahminiStokDegeri=('TahminiStokDegeri','sum'), OrtalamaSatmamaGun=('SatmamaGunSayisi','mean')).reset_index().sort_values('TahminiStokDegeri', ascending=False)

def fmt_group(df):
    x=df.copy()
    if 'TahminiStokDegeri' in x: x['TahminiStokDegeri']=x['TahminiStokDegeri'].apply(format_tl)
    for c in ['UrunSayisi','ToplamStok','OrtalamaSatmamaGun']:
        if c in x: x[c]=x[c].apply(format_number)
    return x.rename(columns={'Tedarikci':'Tedarikçi','AnaKategori':'Ana Kategori','AltKategori':'Alt Kategori','UrunSayisi':'Ürün Sayısı','ToplamStok':'Toplam Stok','TahminiStokDegeri':'Tahmini Stok Değeri','OrtalamaSatmamaGun':'Ort. Satmama Günü'})

def render_stock_inactivity(df, days:int):
    if df.empty:
        st.success(f'Son {days} gündür satmayan stoklu ürün bulunamadı.')
        return
    d=prep(df)
    st.subheader(f'📦 Son {days} Gündür Satmayan Stoklu Ürünler')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Ürün Sayısı', format_number(d['Barkod'].nunique()))
    c2.metric('Toplam Stok', format_number(d['KartKalan'].sum()))
    c3.metric('Tahmini Stok Değeri', format_tl(d['TahminiStokDegeri'].sum()))
    c4.metric('Hiç Satışı Bulunmayan', format_number((d['SatmamaGunSayisi']>=9999).sum()))
    st.warning('Bu rapor stokta olup seçilen gün sayısında satışı olmayan ürünleri gösterir.')
    tabs=st.tabs(['En yüksek stok değeri','Ana kategori özeti','Tedarikçi özeti','Alt kategori özeti','Tüm detay'])
    cols=['Barkod','UrunAdi','Tedarikci','AnaKategori','AltKategori','Marka','KartKalan','KullanilanBirimMaliyet','TahminiStokDegeri','SonSatisTarihi','SatmamaGunSayisi','Durum']
    with tabs[0]: st.dataframe(fmt(d[[c for c in cols if c in d.columns]].head(300)), width='stretch')
    with tabs[1]: st.dataframe(fmt_group(group(d,'AnaKategori')), width='stretch')
    with tabs[2]: st.dataframe(fmt_group(group(d,'Tedarikci')), width='stretch')
    with tabs[3]: st.dataframe(fmt_group(group(d,'AltKategori')), width='stretch')
    with tabs[4]: st.dataframe(fmt(d), width='stretch')
