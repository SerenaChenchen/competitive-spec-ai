from reportlab.pdfgen import canvas
from io import BytesIO
from app.engine import parse_pdf,extract_local
from app.exporter import create_xlsx

def fakepdf(lines):
 b=BytesIO();c=canvas.Canvas(b);y=760
 for line in lines:c.drawString(60,y,line);y-=25
 c.save();return b.getvalue()

def test_evidence_page_and_export():
 doc=parse_pdf('demo.pdf',fakepdf(['Sequential Read: Up to 3500 MB/s','Capacity: 1 TB']))
 r=extract_local(doc,'Demo','Sequential Read')
 assert r.status=='verified' and r.evidence[0].pdf_page==1
 assert '3500' in r.raw_value and r.qualifier=='up_to'
 assert len(create_xlsx([r],[doc],['Demo'],['Sequential Read']))>1000

def test_conflict():
 doc=parse_pdf('demo.pdf',fakepdf(['Capacity: 1 TB','Capacity: 2 TB']))
 assert extract_local(doc,'Demo','Capacity').status=='conflict'

def test_missing():
 doc=parse_pdf('demo.pdf',fakepdf(['Capacity: 1 TB']))
 assert extract_local(doc,'Demo','Voltage').status=='not_disclosed'
