import streamlit as st
import pandas as pd
import glob
import os
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="NMC 모니터링 시스템", page_icon="🚑", layout="wide")
st.title("🚑 응급의료 정책 모니터링 및 보고서")

def get_latest_file(pattern):
    files = glob.glob(pattern)
    if not files: return None
    files.sort()
    return files[-1]

# 데이터 설정
data_configs = [
    {"title": "🏛️ 국회 의안", "pattern": "assembly_results_*.json"},
    {"title": "📅 주요 일정", "pattern": "schedule_results_*.json"},
    {"title": "📰 뉴스 동향", "pattern": "news_results_*.json"}
]

# 선택 항목 저장 바구니
if 'report_list' not in st.session_state:
    st.session_state.report_list = []

st.sidebar.header("📋 보고서 생성함")
st.info("각 항목의 체크박스를 선택하세요. 화면 하단에 보고서가 생성됩니다.")

current_selected = []

# --- 메인 화면: 데이터 표시 ---
for config in data_configs:
    st.header(config["title"])
    latest = get_latest_file(config["pattern"])
    
    if latest:
        try:
            df = pd.read_json(latest)
            for i, row in df.iterrows():
                # [핵심] 국회의 'bill_name'과 뉴스의 'title'을 모두 찾습니다.
                display_name = row.get('bill_name', 
                               row.get('title', 
                               row.get('제목', 
                               row.get('subject', '제목 없음'))))
                
                # 체크박스 생성
                is_selected = st.checkbox(f"{display_name}", key=f"{config['title']}_{i}")
                if is_selected:
                    current_selected.append(row.to_dict())
        except Exception as e:
            st.error(f"{config['title']} 파일을 읽는 중 오류가 발생했습니다.")
    else:
        st.write(f"아직 {config['title']} 데이터 파일이 없습니다.")
    st.markdown("---")

# --- 보고서 미리보기 및 다운로드 ---
if current_selected:
    st.markdown("## 📄 선택된 항목 미리보기")
    report_df = pd.DataFrame(current_selected)
    
    # 화면 표시용 컬럼 정리
    cols = report_df.columns
    display_cols = [c for c in ['bill_name', 'title', 'proposed_date', 'date', 'url'] if c in cols]
    st.table(report_df[display_cols])
    
    # 1. CSV 다운로드 (한글이 가장 안전함)
    csv = report_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 보고서 다운로드 (Excel/CSV)",
        data=csv,
        file_name=f"NMC_Report_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

    # 2. PDF 다운로드 알림
    st.warning("⚠️ 현재 서버 환경에서 PDF 한글 출력은 추가 폰트 설정이 필요합니다. 우선 Excel(CSV) 파일을 업무에 활용해 주세요!")
    
else:
    st.sidebar.write("선택된 항목이 없습니다.")