import streamlit as st
import pandas as pd
import glob
import os
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

class NMC_Official_PDF(FPDF):
    def __init__(self):
        super().__init__()
        if os.path.exists("font.ttf"):
            self.add_font("Korean", "", "font.ttf", uni=True)
            self.kfont = "Korean"
        else: self.kfont = "Arial"

    def header(self):
        # 1. 상단 네이비 그라데이션 구역 (이미지 스타일)
        self.set_fill_color(27, 58, 107) # #1B3A6B
        self.rect(0, 0, 210, 50, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font(self.kfont, size=10)
        self.cell(0, 10, "의료정책연구 | 응급의료 동향 모니터링", ln=True)
        
        self.set_font(self.kfont, size=24)
        self.cell(0, 15, "응급의료 동향 모니터링", ln=True, align='L')
        
        self.set_font(self.kfont, size=11)
        self.cell(0, 10, datetime.now().strftime("%Y.%m.%d"), ln=True)
        self.ln(20)

    def draw_summary_cards(self, a_cnt, s_cnt, n_cnt):
        # 2. 요약 카드 섹션 (이미지의 카드 4개 재현)
        self.set_y(55)
        card_w = 45
        # 카드 배경들
        for i in range(4):
            self.set_fill_color(255, 255, 255)
            self.rect(10 + (i * 48), 55, card_w, 25, 'F')
            self.rect(10 + (i * 48), 55, card_w, 2, 'F') # 상단 선

        self.set_text_color(27, 58, 107)
        self.set_font(self.kfont, size=14)
        # 수치 기입
        self.text(25, 68, str(a_cnt))
        self.text(73, 68, str(s_cnt))
        self.text(121, 68, str(n_cnt))
        self.text(169, 68, str(a_cnt + s_cnt + n_cnt))
        
        self.set_font(self.kfont, size=9)
        self.set_text_color(100, 100, 100)
        self.text(15, 75, "계류 의안")
        self.text(63, 75, "예정 일정")
        self.text(111, 75, "언론 기사")
        self.text(159, 75, "전체 항목")
        self.ln(35)

    def section_title(self, num, title):
        # 3. 섹션 제목 (이미지의 네이비 바 스타일)
        self.set_fill_color(27, 58, 107)
        self.set_text_color(255, 255, 255)
        self.set_font(self.kfont, size=14)
        self.cell(0, 12, f"  {num}  {title}", ln=True, fill=True)
        self.ln(5)
        self.set_text_color(0, 0, 0)

def get_latest_file(pattern):
    files = glob.glob(pattern)
    return sorted(files)[-1] if files else None

# 데이터 로드
df_a = pd.read_json(get_latest_file('assembly_results_*.json')) if get_latest_file('assembly_results_*.json') else pd.DataFrame()
df_s = pd.read_json(get_latest_file('schedule_results_*.json')) if get_latest_file('schedule_results_*.json') else pd.DataFrame()
df_n = pd.read_json(get_latest_file('news_results_*.json')) if get_latest_file('news_results_*.json') else pd.DataFrame()

st.title("🚑 NMC 정책 모니터링 시스템")

# 선택 UI
selected = {'a': [], 's': [], 'n': []}
cols = st.columns(3)
for i, (name, df, key) in enumerate([("의안", df_a, 'a'), ("일정", df_s, 's'), ("뉴스", df_n, 'n')]):
    with cols[i]:
        st.subheader(f"🏛️ {name}")
        if not df.empty:
            for idx, r in df.iterrows():
                if st.checkbox(f"{r.get('bill_name') or r.get('title')}", key=f"{key}{idx}"):
                    selected[key].append(r.to_dict())

if st.button("🚀 이미지 양식 그대로 PDF 생성", use_container_width=True):
    if not any(selected.values()): st.warning("항목을 선택하세요.")
    else:
        pdf = NMC_Official_PDF()
        pdf.add_page()
        
        # 카드 그리기
        pdf.draw_summary_cards(len(selected['a']), len(selected['s']), len(selected['n']))
        
        # 섹션 1
        if selected['a']:
            pdf.section_title("1", "의안 현황")
            for item in selected['a']:
                pdf.set_font(pdf.kfont, size=11)
                pdf.multi_cell(0, 8, txt=f"• {item.get('bill_name')}")
                pdf.set_text_color(27, 58, 107)
                pdf.set_font(pdf.kfont, size=9)
                pdf.cell(0, 6, "   [원문 링크]", ln=True, link=item.get('url', ''))
                pdf.ln(2)

        # 섹션 2
        if selected['s']:
            pdf.ln(5)
            pdf.section_title("2", "주요 일정")
            for item in selected['s']:
                pdf.set_font(pdf.kfont, size=11)
                pdf.multi_cell(0, 8, txt=f"• {item.get('title')} ({item.get('date', '-')})")
                pdf.ln(2)

        pdf_bytes = pdf.output(dest='S')
        st.download_button("💾 PDF 저장", data=bytes(pdf_bytes), file_name="NMC_Official_Report.pdf")