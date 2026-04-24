import streamlit as st
import pandas as pd
import glob
import os
from fpdf import FPDF
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

# 2. PDF 클래스 - 주신 양식의 네이비 헤더와 섹션 디자인 반영
class NMC_Final_PDF(FPDF):
    def __init__(self):
        super().__init__()
        if os.path.exists("font.ttf"):
            self.add_font("Korean", "", "font.ttf", uni=True)
            self.kfont = "Korean"
        else: self.kfont = "Arial"

    def header(self):
        # 최상단 네이비 바 (1B3A6B 색상)
        self.set_fill_color(27, 58, 107) 
        self.rect(0, 0, 210, 45, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font(self.kfont, size=18)
        self.cell(0, 22, '응급의료 동향 모니터링 보고서', ln=True, align='C')
        self.set_font(self.kfont, size=9)
        self.cell(0, 0, f"응급의료정책팀  |  {datetime.now().strftime('%Y.%m.%d')}", ln=True, align='C')
        self.ln(25)

    def draw_section_header(self, num, title, count):
        # 섹션 제목 배경 박스 디자인
        self.set_fill_color(27, 58, 107)
        self.set_text_color(255, 255, 255)
        self.set_font(self.kfont, size=13)
        self.cell(0, 10, f"  {num}. {title} (총 {count}건)", ln=True, fill=True)
        self.ln(4)
        self.set_text_color(0, 0, 0)

def get_latest_file(pattern):
    files = glob.glob(pattern)
    return sorted(files)[-1] if files else None

# 데이터 로드
df_a = pd.read_json(get_latest_file('assembly_results_*.json')) if get_latest_file('assembly_results_*.json') else pd.DataFrame()
df_s = pd.read_json(get_latest_file('schedule_results_*.json')) if get_latest_file('schedule_results_*.json') else pd.DataFrame()
df_n = pd.read_json(get_latest_file('news_results_*.json')) if get_latest_file('news_results_*.json') else pd.DataFrame()

st.title("🚑 NMC 정책 모니터링 보고서 생성기")

# --- 선택 섹션 ---
selected = {'a': [], 's': [], 'n': []}
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("🏛️ 1. 의안")
    if not df_a.empty:
        for i, r in df_a.iterrows():
            if st.checkbox(f"{r.get('bill_name')}", key=f"a{i}"): selected['a'].append(r.to_dict())
with c2:
    st.subheader("📅 2. 일정")
    if not df_s.empty:
        for i, r in df_s.iterrows():
            if st.checkbox(f"{r.get('title')}", key=f"s{i}"): selected['s'].append(r.to_dict())
with c3:
    st.subheader("📰 3. 뉴스")
    if not df_n.empty:
        for i, r in df_n.iterrows():
            if st.checkbox(f"{r.get('title')}", key=f"n{i}"): selected['n'].append(r.to_dict())

# --- PDF 생성 ---
if st.button("🚀 NMC 양식으로 PDF 보고서 발행", use_container_width=True):
    if not any(selected.values()): st.warning("항목을 선택하세요.")
    else:
        try:
            pdf = NMC_Final_PDF()
            pdf.add_page()
            
            # 1. 의안 섹션
            if selected['a']:
                pdf.draw_section_header("1", "의안 현황", len(selected['a']))
                for item in selected['a']:
                    pdf.set_font(pdf.kfont, size=11)
                    pdf.multi_cell(0, 8, txt=f"• {item.get('bill_name')}")
                    pdf.set_text_color(27, 58, 107)
                    pdf.set_font(pdf.kfont, size=9)
                    pdf.cell(0, 6, "   [상세 정보 원문 링크]", ln=True, link=item.get('url', ''))
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(3)

            # 2. 일정 섹션
            if selected['s']:
                pdf.ln(5)
                pdf.draw_section_header("2", "주요 일정", len(selected['s']))
                for item in selected['s']:
                    pdf.set_font(pdf.kfont, size=11)
                    pdf.multi_cell(0, 8, txt=f"• {item.get('title')} ({item.get('date', '-')})")
                    pdf.ln(2)

            # 3. 뉴스 섹션
            if selected['n']:
                pdf.ln(5)
                pdf.draw_section_header("3", "언론 모니터링", len(selected['n']))
                for item in selected['n']:
                    pdf.set_font(pdf.kfont, size=11)
                    # [수정된 부분] 괄호 짝을 정확히 맞췄습니다.
                    source = item.get('source', '뉴스')
                    title = item.get('title')
                    pdf.multi_cell(0, 8, txt=f"• {title} [{source}]")
                    
                    pdf.set_text_color(27, 58, 107)
                    pdf.set_font(pdf.kfont, size=9)
                    pdf.cell(0, 6, "   [기사 원문 링크]", ln=True, link=item.get('url', ''))
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(3)
            
            pdf_bytes = pdf.output(dest='S')
            st.download_button("💾 완성된 보고서 저장", data=bytes(pdf_bytes), file_name=f"NMC_Report_{datetime.now().strftime('%m%d')}.pdf")
            st.success("디자인이 적용된 보고서가 생성되었습니다!")
        except Exception as e: st.error(f"오류: {e}")