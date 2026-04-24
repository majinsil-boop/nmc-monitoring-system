import streamlit as st
import pandas as pd
import glob
import os
from fpdf import FPDF
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="NMC 보고서 생성기", layout="wide")

# PDF 클래스 설정 (한글 지원 및 링크 기능)
class NMC_PDF(FPDF):
    def __init__(self):
        super().__init__()
        # font.ttf 파일이 반드시 폴더에 있어야 합니다.
        if os.path.exists("font.ttf"):
            self.add_font("Korean", "", "font.ttf", uni=True)
            self.kfont = "Korean"
        else:
            self.kfont = "Arial"

    def header(self):
        # 보고서 상단 디자인
        self.set_fill_color(0, 74, 153) # NMC 로고 색상 계열
        self.rect(0, 0, 210, 40, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font(self.kfont, size=20)
        self.cell(0, 15, '응급의료 동향 모니터링 보고서', ln=True, align='C')
        self.set_font(self.kfont, size=12)
        self.cell(0, 10, f"발행일자: {datetime.now().strftime('%Y.%m.%d')}", ln=True, align='C')
        self.ln(20)

def get_latest_file(pattern):
    files = glob.glob(pattern)
    return sorted(files)[-1] if files else None

# 데이터 로드
latest_a = get_latest_file('assembly_results_*.json')
latest_s = get_latest_file('schedule_results_*.json')
latest_n = get_latest_file('news_results_*.json')

df_a = pd.read_json(latest_a) if latest_a else pd.DataFrame()
df_s = pd.read_json(latest_s) if latest_s else pd.DataFrame()
df_n = pd.read_json(latest_n) if latest_n else pd.DataFrame()

st.title("🚑 NMC 데일리 리포트 생성 시스템")
st.write("보고서에 포함할 항목을 선택해 주세요.")

# --- 항목 선택 섹션 ---
selected_data = {'a': [], 's': [], 'n': []}

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🏛️ 국회 의안")
    if not df_a.empty:
        # 의안 데이터에 'bill_name'이 있는지 확인
        name_key = 'bill_name' if 'bill_name' in df_a.columns else 'title'
        for i, row in df_a.iterrows():
            if st.checkbox(f"{row.get(name_key)}", key=f"a_{i}"):
                selected_data['a'].append(row.to_dict())

with col2:
    st.subheader("📅 주요 일정")
    if not df_s.empty:
        for i, row in df_s.iterrows():
            if st.checkbox(f"{row.get('title')}", key=f"s_{i}"):
                selected_data['s'].append(row.to_dict())

with col3:
    st.subheader("📰 언론 뉴스")
    if not df_n.empty:
        for i, row in df_n.iterrows():
            if st.checkbox(f"{row.get('title')}", key=f"n_{i}"):
                selected_data['n'].append(row.to_dict())

st.markdown("---")

# --- PDF 생성 및 다운로드 ---
if st.button("📥 선택 항목으로 PDF 보고서 만들기", use_container_width=True):
    if not any(selected_data.values()):
        st.warning("선택된 항목이 없습니다. 항목을 먼저 체크해 주세요.")
    else:
        try:
            pdf = NMC_PDF()
            pdf.add_page()
            pdf.set_text_color(0, 0, 0)
            
            # 1. 의안 섹션
            if selected_data['a']:
                pdf.set_font(pdf.kfont, size=14)
                pdf.set_fill_color(240, 242, 246)
                pdf.cell(0, 10, "1. 의안 현황", ln=True, fill=True)
                pdf.ln(5)
                for item in selected_data['a']:
                    pdf.set_font(pdf.kfont, size=11)
                    name = item.get('bill_name', item.get('title', '명칭 없음'))
                    pdf.multi_cell(0, 8, txt=f"• {name}")
                    
                    # 상세 링크 추가
                    pdf.set_text_color(0, 0, 255) # 파란색 링크
                    pdf.set_font(pdf.kfont, size=9)
                    url = item.get('url', 'https://likms.assembly.go.kr')
                    pdf.cell(0, 8, txt="   [의안 상세정보 링크 클릭]", ln=True, link=url)
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(2)

            # 2. 뉴스 섹션
            if selected_data['n']:
                pdf.ln(5)
                pdf.set_font(pdf.kfont, size=14)
                pdf.set_fill_color(240, 242, 246)
                pdf.cell(0, 10, "2. 언론 모니터링", ln=True, fill=True)
                pdf.ln(5)
                for item in selected_data['n']:
                    pdf.set_font(pdf.kfont, size=11)
                    pdf.multi_cell(0, 8, txt=f"• {item.get('title')} ({item.get('source', '뉴스')})")
                    
                    # 기사 링크 추가
                    pdf.set_text_color(0, 0, 255)
                    pdf.set_font(pdf.kfont, size=9)
                    url = item.get('url', '#')
                    pdf.cell(0, 8, txt="   [기사 원문 링크 클릭]", ln=True, link=url)
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(2)

            # PDF 출력
            pdf_bytes = pdf.output(dest='S')
            st.download_button(
                label="💾 생성된 PDF 파일 다운로드",
                data=bytes(pdf_bytes), # 데이터를 안전하게 변환
                file_name=f"NMC_Report_{datetime.now().strftime('%m%d')}.pdf",
                mime="application/pdf"
            )
st.download_button(
    label="💾 생성된 PDF 파일 다운로드",
    data=bytes(pdf_bytes), # 데이터를 안전하게 변환
    file_name=f"NMC_Report_{datetime.now().strftime('%m%d')}.pdf",
    mime="application/pdf"
)
            st.success("보고서 작성이 완료되었습니다! 위 버튼을 눌러 저장하세요.")
            
        except Exception as e:
            st.error(f"PDF 생성 중 문제가 발생했습니다: {e}")