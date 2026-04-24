import streamlit as st
import pandas as pd
import glob
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="NMC 동향 모니터링", layout="wide")

# 디자인을 위한 CSS (보내주신 PDF 느낌 재현)
st.markdown("""
    <style>
    .report-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #004a99;
        margin-bottom: 20px;
    }
    .metric-container {
        display: flex;
        justify-content: space-around;
        background-color: #004a99;
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 30px;
    }
    .metric-item { text-align: center; }
    .metric-value { font-size: 24px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def get_latest_file(pattern):
    files = glob.glob(pattern)
    return sorted(files)[-1] if files else None

st.title("🚑 응급의료 동향 모니터링 시스템")
st.write(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# --- 1. 데이터 불러오기 ---
latest_a = get_latest_file('assembly_results_*.json')
latest_s = get_latest_file('schedule_results_*.json')
latest_n = get_latest_file('news_results_*.json')

df_a = pd.read_json(latest_a) if latest_a else pd.DataFrame()
df_s = pd.read_json(latest_s) if latest_s else pd.DataFrame()
df_n = pd.read_json(latest_n) if latest_n else pd.DataFrame()

# --- 2. 항목 선택 섹션 (편집 모드) ---
st.header("🔍 보고서에 담을 항목을 선택하세요")
selected_a, selected_s, selected_n = [], [], []

with st.expander("🏛️ 국회 의안 선택", expanded=True):
    if not df_a.empty:
        for i, row in df_a.iterrows():
            if st.checkbox(f"{row.get('bill_name')}", key=f"a_{i}"):
                selected_a.append(row.to_dict())

with st.expander("📅 주요 일정 선택"):
    if not df_s.empty:
        for i, row in df_s.iterrows():
            if st.checkbox(f"{row.get('title')}", key=f"s_{i}"):
                selected_s.append(row.to_dict())

with st.expander("📰 언론 뉴스 선택"):
    if not df_n.empty:
        for i, row in df_n.iterrows():
            if st.checkbox(f"{row.get('title')}", key=f"n_{i}"):
                selected_n.append(row.to_dict())

st.markdown("---")

# --- 3. 보고서 표출 섹션 (PDF 양식 모드) ---
if selected_a or selected_s or selected_n:
    st.header("📄 생성된 데일리 리포트")
    
    # 상단 요약 카운터 (PDF 상단 디자인)
    total = len(selected_a) + len(selected_s) + len(selected_n)
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-item"><div class="metric-value">{len(selected_a)}</div><div>계류 의안</div></div>
        <div class="metric-item"><div class="metric-value">{len(selected_s)}</div><div>예정 일정</div></div>
        <div class="metric-item"><div class="metric-value">{len(selected_n)}</div><div>언론 기사</div></div>
        <div class="metric-item"><div class="metric-value">{total}</div><div>전체 합계</div></div>
    </div>
    """, unsafe_allow_html=True)

    # 섹션 1: 의안 현황
    if selected_a:
        st.subheader("1️⃣ 의안 현황")
        for item in selected_a:
            st.markdown(f"""
            <div class="report-box">
                <h4>{item.get('bill_name')}</h4>
                <p><b>🏛️ 상태:</b> {item.get('status')} | <b>📅 발의:</b> {item.get('proposed_date')}</p>
                <p style="font-size: 0.9em; color: #555;">{item.get('summary')}</p>
            </div>
            """, unsafe_allow_html=True)

    # 섹션 2: 주요 일정
    if selected_s:
        st.subheader("2️⃣ 주요 일정")
        for item in selected_s:
            st.info(f"📍 {item.get('title')} ({item.get('date')})")

    # 섹션 3: 언론 모니터링
    if selected_n:
        st.subheader("3️⃣ 언론 모니터링")
        for item in selected_n:
            st.write(f"📰 **{item.get('title')}** | {item.get('source')} ({item.get('date')})")
            
    # 브라우저 인쇄 안내
    st.caption("💡 팁: Ctrl + P를 누르면 이 화면 그대로 PDF 저장이 가능합니다.")

else:
    st.warning("위의 체크박스를 선택하면 이곳에 보고서 양식이 나타납니다.")