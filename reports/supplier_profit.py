import pandas as pd
import streamlit as st
from core.formatting import format_number, format_percent, format_tl
from reports.period_profit import run_period_profit

NUMS=['NetSatisKdvDahil','NetSatisKdvHaric','NetSatisMiktari','TahminiSatilanMalMaliyetiKdvHaric','TahminiBrutKarKdvHaric','BrutKarOraniKdvHaric','MaliyetEksikMi','SupheliMaliyetMi']

def run_supplier_profit(conn, start_date, end_date):
    return run_period_profit(conn, start_date, end_date)

def prep(df):
    d=df.copy()
    for c in NUMS:
        if c in d.columns: d[c]=pd.to_numeric(d[c], errors='coerce')
    for c in ['Tedarikci','AnaKategori','AltKategori','Marka']:
        if c in d.columns: d[c]=d[c].fillna('YOK').replace('', 'YOK')
    return d

def build_supplier_summary(df):
    d=prep(df); total_sales=d['NetSatisKdvHaric'].sum(); total_profit=d['TahminiBrutKarKdvHaric'].sum()
    s=d.groupby('Tedarikci', dropna=False).agg(UrunSayisi=('Barkod','nunique'), NetSatisKdvDahil=('NetSatisKdvDahil','sum'), NetSatisKdvHaric=('NetSatisKdvHaric','sum'), TahminiMaliyet=('TahminiSatilanMalMaliyetiKdvHaric','sum'), TahminiBrutKar=('TahminiBrutKarKdvHaric','sum'), MaliyetiOlmayan=('MaliyetEksikMi','sum'), SupheliMaliyet=('SupheliMaliyetMi','sum')).reset_index()
    z=d.assign(ZararEden=(d['TahminiBrutKarKdvHaric'].fillna(0)<0).astype(int)).groupby('Tedarikci', dropna=False)['ZararEden'].sum().reset_index()
    s=s.merge(z,on='Tedarikci',how='left')
    s['KarOrani']=s.apply(lambda r: r['TahminiBrutKar']/r['NetSatisKdvHaric']*100 if r['NetSatisKdvHaric'] else None, axis=1)
    s['SatisPayi']=s['NetSatisKdvHaric'].apply(lambda v: v/total_sales*100 if total_sales else None)
    s['KarPayi']=s['TahminiBrutKar'].apply(lambda v: v/total_profit*100 if total_profit else None)
    s['KontrolGereken']=s['MaliyetiOlmayan'].fillna(0)+s['SupheliMaliyet'].fillna(0)+s['ZararEden'].fillna(0)
    s['YuksekCiroDusukKarMi']=((s['SatisPayi'].fillna(0)>=5)&(s['KarOrani'].fillna(0)<10)).astype(int)
    return s.sort_values('TahminiBrutKar', ascending=False).reset_index(drop=True)

def fmt_summary(df):
    x=df.copy()
    for c in ['NetSatisKdvDahil','NetSatisKdvHaric','TahminiMaliyet','TahminiBrutKar']:
        if c in x: x[c]=x[c].apply(format_tl)
    for c in ['UrunSayisi','MaliyetiOlmayan','SupheliMaliyet','ZararEden','KontrolGereken','YuksekCiroDusukKarMi']:
        if c in x: x[c]=x[c].apply(format_number)
    for c in ['KarOrani','SatisPayi','KarPayi']:
        if c in x: x[c]=x[c].apply(format_percent)
    return x.rename(columns={'Tedarikci':'Tedarikçi','UrunSayisi':'Ürün Sayısı','NetSatisKdvDahil':'Satış KDV Dahil','NetSatisKdvHaric':'Satış KDV Hariç','TahminiMaliyet':'Tahmini Maliyet','TahminiBrutKar':'Tahmini Brüt Kâr','KarOrani':'Kâr Oranı','SatisPayi':'Satış Payı','KarPayi':'Kâr Payı','MaliyetiOlmayan':'Maliyeti Olmayan','SupheliMaliyet':'Şüpheli Maliyet','ZararEden':'Zarar Eden','KontrolGereken':'Kontrol Gereken','YuksekCiroDusukKarMi':'Yüksek Ciro Düşük Kâr'})

def fmt_products(df):
    x=df.copy()
    for c in ['NetSatisKdvHaric','TahminiSatilanMalMaliyetiKdvHaric','TahminiBrutKarKdvHaric']:
        if c in x: x[c]=x[c].apply(format_tl)
    if 'NetSatisMiktari' in x: x['NetSatisMiktari']=x['NetSatisMiktari'].apply(format_number)
    if 'BrutKarOraniKdvHaric' in x: x['BrutKarOraniKdvHaric']=x['BrutKarOraniKdvHaric'].apply(format_percent)
    return x.rename(columns={'UrunAdi':'Ürün Adı','Tedarikci':'Tedarikçi','AnaKategori':'Ana Kategori','AltKategori':'Alt Kategori','NetSatisMiktari':'Satış Miktarı','NetSatisKdvHaric':'Satış KDV Hariç','TahminiSatilanMalMaliyetiKdvHaric':'Tahmini Maliyet','TahminiBrutKarKdvHaric':'Tahmini Brüt Kâr','BrutKarOraniKdvHaric':'Kâr Oranı','MaliyetSaglikDurumu':'Maliyet Sağlık Durumu'})

def render_supplier_profit(df, report_label):
    if df.empty:
        st.warning('Tedarikçi kârlılığı için veri bulunamadı.'); return
    d=prep(df); s=build_supplier_summary(d)
    total_sales=d['NetSatisKdvHaric'].sum(); total_profit=d['TahminiBrutKarKdvHaric'].sum(); margin=total_profit/total_sales*100 if total_sales else None
    st.subheader(f'🚚 Tedarikçi Bazlı Kârlılık Raporu - {report_label}')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Tedarikçi Sayısı',format_number(s['Tedarikci'].nunique()))
    c2.metric('Satış KDV Hariç',format_tl(total_sales))
    c3.metric('Tahmini Brüt Kâr',format_tl(total_profit))
    c4.metric('Kâr Oranı',format_percent(margin))
    st.warning('Bu rapor stok kartı bazlı tahmini brüt kârlılıktır; muhasebe net kârı değildir.')
    tabs=st.tabs(['Tedarikçi özeti','Yüksek ciro / düşük kâr','Çok zarar eden tedarikçiler','Tedarikçi açılır detay','Tüm ürün detay'])
    with tabs[0]: st.dataframe(fmt_summary(s), width='stretch')
    with tabs[1]:
        r=s[s['YuksekCiroDusukKarMi']==1].sort_values('NetSatisKdvHaric',ascending=False)
        st.dataframe(fmt_summary(r), width='stretch') if not r.empty else st.success('Yüksek ciro / düşük kâr olarak işaretlenen tedarikçi yok.')
    with tabs[2]: st.dataframe(fmt_summary(s.sort_values(['ZararEden','TahminiBrutKar'], ascending=[False,True]).head(50)), width='stretch')
    with tabs[3]:
        for _,row in s.sort_values('NetSatisKdvHaric', ascending=False).iterrows():
            sup=str(row['Tedarikci'])
            with st.expander(f"{sup} | Satış: {format_tl(row['NetSatisKdvHaric'])} | Kâr: {format_tl(row['TahminiBrutKar'])} | Oran: {format_percent(row['KarOrani'])} | Zarar Eden: {format_number(row['ZararEden'])}"):
                p=d[d['Tedarikci'].astype(str)==sup].sort_values('TahminiBrutKarKdvHaric', ascending=True)
                cols=['Barkod','UrunAdi','AnaKategori','AltKategori','NetSatisMiktari','NetSatisKdvHaric','TahminiSatilanMalMaliyetiKdvHaric','TahminiBrutKarKdvHaric','BrutKarOraniKdvHaric','MaliyetSaglikDurumu']
                st.dataframe(fmt_products(p[[c for c in cols if c in p.columns]]), width='stretch')
    with tabs[4]: st.dataframe(fmt_products(d.sort_values('TahminiBrutKarKdvHaric', ascending=True)), width='stretch')
