import streamlit as st
import pandas as pd
import glob
import os
from fpdf import FPDF
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="NMC 모니터링 시스템", page_icon="🚑", layout="wide")
st.title("🚑 응급의료 정책 모니터링 및 PDF 보고서 생성")

# 2. 최신 파일 찾는 함수
def get_latest_file(pattern):
    files = glob.glob(pattern)
    if not files: return None
    files.sort()
    return files[-1]

# 3. 보고서 바구니 (선택한 항목 저장용)
if 'report_list' not in st.session_state:
    st.session_state.report_list = []

# 4. 데이터 섹션 설정
data_configs = [
    {"title": "🏛️ 국회 의안", "pattern": "assembly_results_*.json"},
    {"title": "📅 주요 일정", "pattern": "schedule_results_*.json"},
    {"title": "📰 뉴스 동향", "pattern": "news_results_*.json"}
]

st.sidebar.header("📋 보고서 생성함")
st.info("각 항목 옆의 체크박스를 선택하면 하단 보고서 목록에 추가됩니다.")

# --- 화면에 데이터 뿌리기 ---
current_selected = []

for config in data_configs:
    st.header(config["title"])
    latest = get_latest_file(config["pattern"])
    
    if latest:
        df = pd.read_json(latest)
        # 각 행을 체크박스와 함께 표시
        for i, row in df.iterrows():
            # 체크박스를 만들고, 선택되면 리스트에 담기
            is_selected = st.checkbox(f"{row['title']}", key=f"{config['title']}_{i}")
            if is_selected:
                current_selected.append(row.to_dict())
    else:
        st.write(f"아직 {config['title']} 데이터 파일이 없습니다.")
    st.markdown("---")

# 5. PDF 생성 클래스 (영문 기준, 한글은 추후 폰트 작업 필요)
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'NMC Emergency Medical Policy Report', 0, 1, 'C')
        self.ln(10)

def create_pdf(selected_items):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(0, 10, txt=f"Report Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
    pdf.ln(10)

    for i, item in enumerate(selected_items):
        title = item.get('title', 'No Title')
        link = item.get('link', 'No Link')
        pdf.multi_cell(0, 10, txt=f"{i+1}. {title}")
        pdf.set_text_color(0, 0, 255)
        pdf.cell(0, 10, txt=f"   Link: {link}", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
    
    return pdf.output(dest='S').encode('latin-1')

# 6. 보고서 결과 확인 및 다운로드
if current_selected:
    st.sidebar.success(f"{len(current_selected)}개 항목 선택됨")
    
    st.markdown("## 📄 생성된 보고서 미리보기")
    report_df = pd.DataFrame(current_selected)
    st.table(report_df[['title', 'link']] if 'link' in report_df.columns else report_df)
    
    # PDF 다운로드
    try:
        pdf_bytes = create_pdf(current_selected)
        st.download_button(
            label="📥 PDF 보고서 다운로드",
            data=pdf_bytes,
            file_name=f"NMC_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    except:
        st.warning("PDF 생성 중 오류가 발생했습니다. (영문 외 문자가 포함되었을 수 있습니다.)")
else:
    st.sidebar.write("선택된 항목이 없습니다.")