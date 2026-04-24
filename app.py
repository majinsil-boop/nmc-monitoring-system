import streamlit as st
import pandas as pd
import glob
import os
from fpdf import FPDF
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

# 화면 디자인 (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .section-header {
        color: #004a99;
        font-size: 22px;
        font-weight: bold;
        border-bottom: 2px solid #004a99;
        margin: 20px 0 10px 0;
        padding-bottom: 5px;
    }
    .report-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# PDF 클래스 (디자인 및 한글 폰트)
class NMC_PDF(FPDF):
    def __init__(self):
        super().__init__()
        if os.path.exists("font.ttf"):
            self.add_font("Korean", "", "font.ttf", uni=True)
            self.kfont = "Korean"
        else: self.kfont = "Arial"

    def header(self):
        self.set_fill_color(0, 74, 153)
        self.rect(0, 0, 210, 40, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font(self.kfont, size=18)
        self.cell(0, 15, '응급의료 동향 모니터링', ln=True, align='C')
        self.set_font(self.kfont, size=11)
        self.cell(0, 10, f"{datetime.now().strftime('%Y.%m.%d')}", ln=True, align='C')
        self.ln(20)

def get_latest_file(pattern):
    files = glob.glob(pattern)
    return sorted(files)[-1] if files else None

# 데이터 로드 (의안, 일정, 뉴스)
df_a = pd.read_json(get_latest_file('assembly_results_*.json')) if get_latest_file('assembly_results_*.json') else pd.DataFrame()
df_s = pd.read_json(get_latest_file('schedule_results_*.json')) if get_latest_file('schedule_results_*.json') else pd.DataFrame()
df_n = pd.read_json(get_latest_file('news_results_*.json')) if get_latest_file('news_results_*.json') else pd.DataFrame()

st.title("🚑 NMC 데일리 리포트 시스템")

# --- 항목 선택 섹션 ---
selected_data = {'a': [], 's': [], 'n': []}
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🏛️ 1. 의안")
    if not df_a.empty:
        for i, row in df_a.iterrows():
            if st.checkbox(f"{row.get('bill_name', '의안')}", key=f"a_{i}"):
                selected_data['a'].append(row.to_dict())

with col2:
    st.subheader("📅 2. 일정")
    if not df_s.empty:
        for i, row in df_s.iterrows():
            if st.checkbox(f"{row.get('title', '일정')}", key=f"s_{i}"):
                selected_data['s'].append(row.to_dict())

with col3:
    st.subheader("📰 3. 뉴스")
    if not df_n.empty:
        for i, row in df_n.iterrows():
            if st.checkbox(f"{row.get('title', '뉴스')}", key=f"n_{i}"):
                selected_data['n'].append(row.to_dict())

st.markdown("---")

# --- PDF 생성 버튼 및 로직 ---
if st.button("📥 선택한 항목으로 보고서(PDF) 발행", use_container_width=True):
    if not any(selected_data.values()):
        st.warning("항목을 먼저 선택해 주세요.")
    else:
        try:
            pdf = NMC_PDF()
            pdf.add_page()
            
            # 섹션 1: 의안 현황
            if selected_data['a']:
                # [수정] style='B'를 제거했습니다.
                pdf.set_font(pdf.kfont, size=14) 
                pdf.set_fill_color(240, 242, 246)
                pdf.cell(0, 10, " 1. 의안 현황", ln=True, fill=True)
                pdf.ln(3)
                for item in selected_data['a']:
                    pdf.set_font(pdf.kfont, size=11)
                    pdf.multi_cell(0, 8, txt=f"• {item.get('bill_name')}")
                    pdf.set_text_color(0, 0, 255)
                    pdf.set_font(pdf.kfont, size=9)
                    pdf.cell(0, 7, txt="  [의안 상세 보기]", ln=True, link=item.get('url', ''))
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(2)

            # 섹션 2: 주요 일정
            if selected_data['s']:
                pdf.ln(5)
                pdf.set_font(pdf.kfont, size=14) # [수정] style='B' 제거
                pdf.set_fill_color(240, 242, 246)
                pdf.cell(0, 10, " 2. 주요 일정", ln=True, fill=True)
                pdf.ln(3)
                for item in selected_data['s']:
                    pdf.set_font(pdf.kfont, size=11)
                    pdf.multi_cell(0, 8, txt=f"• {item.get('title')} ({item.get('date', '-')})")
                    pdf.ln(2)

            # 섹션 3: 언론 모니터링
            if selected_data['n']:
                pdf.ln(5)
                pdf.set_font(pdf.kfont, size=14) # [수정] style='B' 제거
                pdf.set_fill_color(240, 242, 246)
                pdf.cell(0, 10, " 3. 언론 모니터링", ln=True, fill=True)
                pdf.ln(3)
                for item in selected_data['n']:
                    pdf.set_font(pdf.kfont, size=11)
                    pdf.multi_cell(0, 8, txt=f"• {item.get('title')} [{item.get('source', '뉴스')}]")
                    pdf.set_text_color(0, 0, 255)
                    pdf.set_font(pdf.kfont, size=9)
                    pdf.cell(0, 7, txt="  [기사 원문 보기]", ln=True, link=item.get('url', ''))
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(2)

            pdf_bytes = pdf.output(dest='S')
            st.download_button(
                label="💾 생성된 PDF 보고서 저장하기",
                data=bytes(pdf_bytes),
                file_name=f"NMC_Report_{datetime.now().strftime('%m%d')}.pdf",
                mime="application/pdf"
            )
            st.success("보고서 작성이 완료되었습니다!")
        except Exception as e:
            st.error(f"오류 발생: {e}")