import streamlit as st
import pandas as pd
import glob
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="응급의료 동향 모니터링", layout="wide")

# 스타일링 (PDF의 깔끔한 느낌을 위한 CSS)
st.markdown("""
    <style>
    .report-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #004a99;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

def get_latest_file(pattern):
    files = glob.glob(pattern)
    return sorted(files)[-1] if files else None

# --- 상단 헤더 섹션 ---
st.title("🚑 응급의료 동향 모니터링")
col_date, col_time = st.columns([8, 2])
with col_date:
    st.subheader(f"📅 {datetime.now().strftime('%Y.%m.%d')}")
with col_time:
    st.write(f"⏱️ {datetime.now().strftime('%H:%M')} 생성")

# --- 1. 상단 요약 수치 (PDF의 상단 카운터 재현) ---
latest_a = get_latest_file('assembly_results_*.json')
latest_s = get_latest_file('schedule_results_*.json')
latest_n = get_latest_file('news_results_*.json')

df_a = pd.read_json(latest_a) if latest_a else pd.DataFrame()
df_s = pd.read_json(latest_s) if latest_s else pd.DataFrame()
df_n = pd.read_json(latest_n) if latest_n else pd.DataFrame()

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("계류 의안", f"{len(df_a)}건")
with c2: st.metric("예정 일정", f"{len(df_s)}건")
with c3: st.metric("언론 기사", f"{len(df_n)}건")
with c4: st.metric("전체 업데이트", f"{len(df_a)+len(df_s)+len(df_n)}건")

st.markdown("---")

# --- 2. 섹션별 본문 (PDF 레이아웃 재현) ---

# [1] 의안 현황
st.markdown("### 1️⃣ 의안 현황")
if not df_a.empty:
    for _, row in df_a.iterrows():
        with st.container():
            st.markdown(f"""
            <div class="report-box">
                <h4>{row.get('bill_name', '의안명 없음')}</h4>
                <p><b>📅 발의일:</b> {row.get('proposed_date', '-')} | <b>🏛️ 위원회:</b> {row.get('committee', '-')} | <b>상태:</b> {row.get('status', '-')}</p>
                <p style="color: #666;">{row.get('summary', '요약 정보가 없습니다.')}</p>
                <a href="{row.get('url', '#')}">🔗 상세 보기</a>
            </div>
            """, unsafe_allow_html=True)

# [2] 주요 일정
st.markdown("### 2️⃣ 주요 일정")
if not df_s.empty:
    for _, row in df_s.iterrows():
        st.info(f"📍 {row.get('title', '일정명 없음')} | {row.get('date', '-')} | {row.get('location', '-')}")

# [3] 언론 모니터링
st.markdown("### 3️⃣ 언론 모니터링")
if not df_n.empty:
    # 키워드별로 묶어서 표출하거나 리스트로 나열
    for _, row in df_n.iterrows():
        col_news, col_link = st.columns([8, 2])
        with col_news:
            st.write(f"📰 **{row.get('title')}** ({row.get('source', '-')})")
        with col_link:
            st.link_button("기사보기", row.get('url', ''))