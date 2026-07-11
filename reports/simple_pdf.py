from __future__ import annotations
import io, os, re
from datetime import datetime
import pandas as pd

def safe_filename(label: str, prefix='ertan_rapor'):
    clean=re.sub(r'[^0-9A-Za-zğüşöçıİĞÜŞÖÇ_-]+','_',str(label)).strip('_')
    return f'{prefix}_{clean or "rapor"}.pdf'

def _fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    reg=next((p for p in [r'C:\Windows\Fonts\arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'] if os.path.exists(p)), None)
    bold=next((p for p in [r'C:\Windows\Fonts\arialbd.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'] if os.path.exists(p)), None)
    if reg: pdfmetrics.registerFont(TTFont('ErtanRegular',reg)); fr='ErtanRegular'
    else: fr='Helvetica'
    if bold: pdfmetrics.registerFont(TTFont('ErtanBold',bold)); fb='ErtanBold'
    else: fb='Helvetica-Bold'
    return fr,fb

def _tl(v):
    try: return '-' if pd.isna(v) else f'{float(v):,.2f} TL'.replace(',','X').replace('.',',').replace('X','.')
    except Exception: return '-'
def _num(v):
    try: return '-' if pd.isna(v) else f'{float(v):,.2f}'.replace(',','X').replace('.',',').replace('X','.')
    except Exception: return '-'
def _pct(v):
    try: return '-' if pd.isna(v) else f'%{float(v):,.2f}'.replace(',','X').replace('.',',').replace('X','.')
    except Exception: return '-'

def _p(text, style):
    from reportlab.platypus import Paragraph
    return Paragraph(str(text).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'), style)

def _table(rows, widths, fr, fb, size=6):
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    t=Table(rows, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),fr),('FONTNAME',(0,0),(-1,0),fb),('FONTSIZE',(0,0),(-1,-1),size),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAECEF')),('GRID',(0,0),(-1,-1),0.25,colors.HexColor('#D1D5DB')),('VALIGN',(0,0),(-1,-1),'TOP')]))
    return t

def _base(title, label):
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=landscape(A4),leftMargin=1*cm,rightMargin=1*cm,topMargin=1*cm,bottomMargin=1*cm)
    fr,fb=_fonts(); styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name='TitleTR', parent=styles['Title'], fontName=fb, fontSize=16, alignment=TA_LEFT)); styles['Heading2'].fontName=fb; styles['Normal'].fontName=fr; styles['Normal'].fontSize=8
    story=[_p(title,styles['TitleTR']), _p(f'Rapor: {label} | Oluşturma: {datetime.now().strftime("%d.%m.%Y %H:%M")}',styles['Normal'])]
    return buf,doc,story,styles,fr,fb

def build_stock_pdf(df,label):
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    d=df.copy(); buf,doc,story,styles,fr,fb=_base('Ertan Market - Satmayan Stok Raporu',label); story.append(Spacer(1,0.3*cm))
    rows=[['Barkod','Ürün','Tedarikçi','Ana Kat.','Alt Kat.','Stok','Stok Değeri','Son Satış','Gün']]
    for _,r in d.sort_values('TahminiStokDegeri', ascending=False).head(150).iterrows():
        rows.append([str(r.get('Barkod','')),str(r.get('UrunAdi',''))[:42],str(r.get('Tedarikci',''))[:30],str(r.get('AnaKategori',''))[:18],str(r.get('AltKategori',''))[:18],_num(r.get('KartKalan')),_tl(r.get('TahminiStokDegeri')),str(r.get('SonSatisTarihi',''))[:10],_num(r.get('SatmamaGunSayisi'))])
    story.append(_table(rows,[2.3*cm,5*cm,3.2*cm,2.2*cm,2.2*cm,1.3*cm,2.4*cm,1.8*cm,1.1*cm],fr,fb,5.7)); doc.build(story); return buf.getvalue()

def build_supplier_pdf(df,label):
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer, PageBreak
    from reports.supplier_profit import build_supplier_summary
    d=df.copy(); s=build_supplier_summary(d); buf,doc,story,styles,fr,fb=_base('Ertan Market - Tedarikçi Kârlılık Raporu',label); story.append(Spacer(1,0.3*cm))
    rows=[['Tedarikçi','Ürün','Satış','Maliyet','Brüt Kâr','Oran','Zarar','Kontrol']]
    for _,r in s.head(100).iterrows(): rows.append([str(r.get('Tedarikci',''))[:42],str(int(r.get('UrunSayisi',0) or 0)),_tl(r.get('NetSatisKdvHaric')),_tl(r.get('TahminiMaliyet')),_tl(r.get('TahminiBrutKar')),_pct(r.get('KarOrani')),str(int(r.get('ZararEden',0) or 0)),str(int(r.get('KontrolGereken',0) or 0))])
    story.append(_table(rows,[5.2*cm,1.1*cm,2.6*cm,2.6*cm,2.6*cm,1.6*cm,1.1*cm,1.2*cm],fr,fb,6.2)); story.append(PageBreak())
    rows=[['Barkod','Ürün','Tedarikçi','Ana Kat.','Satış','Maliyet','Brüt Kâr','Oran']]
    for _,r in d.sort_values('TahminiBrutKarKdvHaric', ascending=True).head(120).iterrows(): rows.append([str(r.get('Barkod','')),str(r.get('UrunAdi',''))[:42],str(r.get('Tedarikci',''))[:32],str(r.get('AnaKategori',''))[:18],_tl(r.get('NetSatisKdvHaric')),_tl(r.get('TahminiSatilanMalMaliyetiKdvHaric')),_tl(r.get('TahminiBrutKarKdvHaric')),_pct(r.get('BrutKarOraniKdvHaric'))])
    story.append(_p('En zayıf ürünler - ilk 120',styles['Heading2'])); story.append(_table(rows,[2.3*cm,5*cm,3.8*cm,2.2*cm,2.3*cm,2.3*cm,2.3*cm,1.4*cm],fr,fb,5.7)); doc.build(story); return buf.getvalue()
