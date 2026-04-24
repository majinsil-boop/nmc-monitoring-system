import streamlit as st
import pandas as pd
import glob
import os
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="NMC 모니터링 & PDF 보고서", page_icon="🚑", layout="wide")

st.title("🚑 응급의료 정책 모니터링 및 PDF 보고서 생성")

def get_latest_file(pattern):
    files = glob.glob(pattern)
    if not files: return None
    files.sort()
    return files[-1]

# 세션 상태 초기화
if 'report_list' not in st.session_state:
    st.session_state.report_list = pd.DataFrame()

# --- 데이터 불러오기 섹션 ---
st.header("🔍 최신 동향 확인 및 항목 선택")
st.info("표의 왼쪽을 클릭하여 보고서에 넣을 항목을 다중 선택하세요.")

# 국회/일정/뉴스 데이터를 한 리스트에 담아 처리
data_configs = [
    {"title": "🏛️ 국회 의안", "pattern": "assembly_results_*.json"},
    {"title": "📅 주요 일정", "pattern": "schedule_results_*.json"},
    {"title": "📰 뉴스 동향", "pattern": "news_results_*.json"}
]

all_selected_data = []

for config in data_configs:
    st.subheader(config["title"])
    latest = get_latest_file(config["pattern"])
    if latest:
        df = pd.read_json(latest)
        # 에러를 방지하기 위해 가장 표준적인 설정으로 변경합니다.
        event = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun", 
            selection_mode=["multi_row", "multi_column"], # 리스트 형태로 명시
            key=config["title"]
        )
        # 선택된 행이 있는지 확인하는 안전한 방법
        if event and hasattr(event, 'selection') and event.selection.get("rows"):
            all_selected_data.append(df.iloc[event.selection["rows"]])
    st.markdown("---")

# --- PDF 생성 함수 ---
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    # 한글 폰트 설정 (기본 폰트는 한글이 깨지므로 나눔고딕 등을 시스템에서 불러오거나 기본 폰트 사용)
    # 여기서는 구조만 잡습니다. 실제 배포 시 폰트 파일(.ttf)이 폴더에 있어야 완벽합니다.
    pdf.set_font("Arial", size=12) 
    
    pdf.cell(200, 10, txt="NMC Emergency Medical Policy Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
    pdf.ln(10)

    for i, row in data.iterrows():
        pdf.multi_cell(0, 10, txt=f"[{i+1}] {row.get('title', 'No Title')}")
        if 'link' in row:
            pdf.set_text_color(0, 0, 255)
            pdf.cell(0, 10, txt=f"Link: {row['link']}", ln=True)
            pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 사이드바: 보고서 생성함 ---
st.sidebar.header("📋 보고서 바구니")
if st.sidebar.button("📝 선택 항목 확정"):
    if all_selected_data:
        st.session_state.report_list = pd.concat(all_selected_data)
        st.sidebar.success(f"{len(st.session_state.report_list)}개 항목이 확정되었습니다.")
    else:
        st.sidebar.warning("선택된 항목이 없습니다.")

if not st.session_state.report_list.empty:
    st.markdown("### 📄 보고서 미리보기")
    st.table(st.session_state.report_list[['title', 'link']] if 'link' in st.session_state.report_list.columns else st.session_state.report_list)
    
    # PDF 다운로드 버튼
    pdf_bytes = create_pdf(st.session_state.report_list)
    st.download_button(
        label="📥 PDF 보고서 다운로드",
        data=pdf_bytes,
        file_name=f"NMC_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )