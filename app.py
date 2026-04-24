import streamlit as st
import pandas as pd
import glob
import os
from fpdf import FPDF
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

# PDF 클래스 - 보여주신 generate_report.py의 네이비 스타일 반영
class NMC_Final_PDF(FPDF):
    def __init__(self):
        super().__init__()
        if os.path.exists("font.ttf"):
            self.add_font("Korean", "", "font.ttf", uni=True)
            self.kfont = "Korean"
        else: self.kfont = "Arial"

    def header(self):
        # 1. 상단 그라데이션 느낌의 네이비 헤더 (1B3A6B 색상 반영)
        self.set_fill_color(27, 58, 107) 
        self.rect(0, 0, 210, 45, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font(self.kfont, size=20)
        self.cell(0, 20, '응급의료 동향 모니터링 보고서', ln=True, align='C')
        self.set_font(self.kfont, size=10)
        self.cell(0, 5, f"응급의료정책팀  |  자동 모니터링 시스템", ln=True, align='C')
        self.ln(25)

    def section_title(self, num, title, count):
        # 2. 섹션 헤더 (1B3A6B 배경 박스)
        self.set_fill_color(27, 58, 107)
        self.set_text_color(255, 255, 255)
        self.set_font(self.kfont, size=13)
        self.cell(0, 10, f"  {num}. {title} (총 {count}건)", ln=True, fill=True)
        self.ln(4)

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
    st.subheader("🏛️ 의안 선택")
    for i, r in df_a.iterrows():
        if st.checkbox(f"{r.get('bill_name')}", key=f"a{i}"): selected['a'].append(r.to_dict())
with c2:
    st.subheader("📅 일정 선택")
    for i, r in df_s.iterrows():
        if st.checkbox(f"{r.get('title')}", key=f"s{i}"): selected['s'].append(r.to_dict())
with c3:
    st.subheader("📰 뉴스 선택")
    for i, r in df_n.iterrows():
        if st.checkbox(f"{r.get('title')}", key=f"n{i}"): selected['n'].append(r.to_dict())

# --- PDF 생성 실행 ---
if st.button("🚀 선택한 항목으로 전문 보고서 발행", use_container_width=True):
    if not any(selected.values()): st.warning("항목을 선택하세요.")
    else:
        try:
            pdf = NMC_Final_PDF()
            pdf.add_page()
            
            # 요약 통계 박스
            pdf.set_font(pdf.kfont, size=10)
            pdf.set_text_color(100, 100, 100)
            summary_txt = f"계류 의안: {len(selected['a'])}건  /  예정 일정: {len(selected['s'])}건  /  언론 기사: {len(selected['n'])}건"
            pdf.cell(0, 10, summary_txt, ln=True, align='R')
            pdf.ln(5)

            # 섹션별 그리기
            data_map = [("1", "의안 현황", 'a'), ("2", "주요 일정", 's'), ("3", "언론 모니터링", 'n')]
            for num, title, key in data_map:
                if selected[key]:
                    pdf.section_title(num, title, len(selected[key]))
                    for item in selected[key]:
                        pdf.set_font(pdf.kfont, size=11)
                        pdf.set_text_color(0, 0, 0)
                        name = item.get('bill_name') or item.get('title')
                        pdf.multi_cell(0, 8, txt=f"• {name}")
                        
                        # 파란색 링크 (generate_report 스타일)
                        pdf.set_text_color(27, 58, 107)
                        pdf.set_font(pdf.kfont, size=9)
                        pdf.cell(0, 6, "   [상세 정보 원문 링크 클릭]", ln=True, link=item.get('url', ''))
                        pdf.set_text_color(0, 0, 0)
                        pdf.ln(2)
            
            pdf_bytes = pdf.output(dest='S')
            st.download_button("💾 완성된 보고서(PDF) 저장", data=bytes(pdf_bytes), file_name=f"NMC_보고서_{datetime.now().strftime('%m%d')}.pdf")
            st.success("양식에 맞춰 보고서가 생성되었습니다!")
        except Exception as e: st.error(f"오류: {e}")