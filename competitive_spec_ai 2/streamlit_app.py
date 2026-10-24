import os,re
import pandas as pd
import streamlit as st
from app.engine import TEMPLATES,parse_pdf,comparison
from app.exporter import create_xlsx

st.set_page_config(page_title='SpecCompare AI',page_icon='📊',layout='wide')
st.title('SpecCompare AI｜競品規格比較表自動生成')
st.caption('上傳公開競品 PDF → 自訂欄位 → 擷取與驗證來源 → 互動比較 → Excel 匯出')
with st.sidebar:
 st.header('分析設定')
 category=st.selectbox('產品模板',list(TEMPLATES))
 default=', '.join(TEMPLATES[category])
 fields_raw=st.text_area('比較欄位（每行一項，也支援逗號）',value=default,height=175,key=f'fields_{category}')
 fields=list(dict.fromkeys(x.strip() for x in re.split('[,\n]',fields_raw) if x.strip()))
 st.caption(f'目前 {len(fields)} 個欄位')
 method=st.radio('擷取引擎',['本機規則（免 API Key）','AI 語意擷取（OpenAI API）'])
 key=st.text_input('OpenAI API Key',type='password',value=os.getenv('OPENAI_API_KEY','')) if method.startswith('AI') else None
 model=st.text_input('模型名稱',value='gpt-4.1-mini') if key is not None else 'gpt-4.1-mini'
 st.info('本機規則適合格式清楚的文字型 PDF；AI 模式可辨識更多規格表達方式。掃描 PDF 尚未支援 OCR。')
files=st.file_uploader('上傳 2–10 份 PDF 規格文件',type=['pdf'],accept_multiple_files=True)
if files:
 if len(files)>10:st.error('單次最多 10 份文件');st.stop()
 docs=[]
 for f in files:
  data=f.getvalue()
  if len(data)>25*1024*1024:st.error(f'{f.name} 超過 25MB');st.stop()
  try: docs.append(parse_pdf(f.name,data))
  except Exception as e:st.error(f'{f.name} 無法解析：{e}');st.stop()
 st.subheader('產品名稱 / 型號確認')
 products=[]
 cols=st.columns(min(len(docs),3))
 for i,d in enumerate(docs):
  with cols[i%len(cols)]:
   products.append(st.text_input(f'{d["filename"]} ({d["page_count"]} 頁)',value=os.path.splitext(d['filename'])[0],key=f'product_{d["id"]}_{i}'))
   if not any(p['text'].strip() for p in d['pages']):st.warning('此 PDF 沒有可擷取的文字層；需要 OCR。')
 if len(set(products))!=len(products):st.error('產品名稱不能重複。')
 elif not fields:st.error('請設定至少一個比較欄位。')
 elif st.button('開始產生比較表',type='primary'):
  if key is not None and not key:st.error('AI 模式請填寫 API Key。')
  else:
   with st.spinner('解析規格與檢查來源中…'):
    try:
     result=comparison(docs,products,fields,api_key=key if key is not None else None,model=model)
     st.session_state['report']=(result,docs,products,fields)
    except Exception as exc:st.error(f'擷取失敗：{exc}')
if 'report' in st.session_state:
 results,docs,products,fields=st.session_state['report']
 st.divider();st.header('競品比較表')
 look={(r.product_id,r.field):r for r in results}
 data=[]
 for f in fields:
  row={'Specification':f}
  for p in products:
   v=look[(p,f)]
   row[p]=v.normalized_value if v.status in ('verified','manual_override') else (('⚠ '+v.raw_value) if v.raw_value else '— '+v.status)
  data.append(row)
 st.caption('⚠ 表示衝突或待人工審查。每個有值的儲存格都可在下方查看引用來源。')
 edited=st.data_editor(pd.DataFrame(data),hide_index=True,use_container_width=True,disabled=['Specification'],key='editor')
 # Manual edits modify comparison output, but original evidence remains immutable.
 for _,row in edited.iterrows():
  for p in products:
   r=look[(p,row['Specification'])]
   baseline=r.normalized_value if r.status in ('verified','manual_override') else ('⚠ '+r.raw_value if r.raw_value else '— '+r.status)
   if str(row[p])!=str(baseline):r.normalized_value=str(row[p]);r.status='manual_override';r.note='User-edited comparison value; original evidence preserved.'
 st.subheader('來源查證 Evidence Inspector')
 c1,c2=st.columns(2)
 with c1:picked_product=st.selectbox('產品',products)
 with c2:picked_field=st.selectbox('規格',fields)
 target=look[(picked_product,picked_field)]
 st.write('狀態：',target.status,' | 原始值：',target.raw_value or '未擷取',' | 限定詞：',target.qualifier)
 if target.note:st.warning(target.note)
 if not target.evidence:st.info('未找到可確認的頁面證據。')
 for ev in target.evidence:
  with st.expander(f'{ev.filename}｜PDF 第 {ev.pdf_page} 頁｜'+('原文已核對' if ev.verified else '原文待核對')):
   st.code(ev.quote,language=None)
   doc=next(d for d in docs if d['id']==ev.document_id)
   st.download_button('下載原始 PDF 以核對',doc['bytes'],file_name=doc['filename'],key=f'dl_{picked_product}_{picked_field}_{ev.document_id}_{ev.pdf_page}')
   try:
    import fitz
    pdf=fitz.open(stream=doc['bytes'],filetype='pdf')
    img=pdf[ev.pdf_page-1].get_pixmap(matrix=fitz.Matrix(1.25,1.25)).tobytes('png')
    st.image(img,caption=f'PDF 第 {ev.pdf_page} 頁',use_container_width=True)
   except Exception as exc:st.caption(f'頁面預覽無法顯示：{exc}')
 st.subheader('匯出')
 st.download_button('下載 Excel（含來源頁碼、數據品質與原文）',create_xlsx(results,docs,products,fields),file_name='competitive_spec_comparison.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',type='primary')
 st.download_button('下載 CSV',edited.to_csv(index=False).encode('utf-8-sig'),file_name='competitive_spec_comparison.csv',mime='text/csv')
 st.caption('使用限制：不會推論缺失規格；不會自動判斷同一份文件內多個 SKU 的規格歸屬；請將型號專屬 PDF 分別上傳。AI 模式的原文存在性驗證不等於工程語意正確，重要決策仍應人工覆核。')
