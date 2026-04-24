import streamlit as st
import pandas as pd
import glob
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="NMC 응급의료 모니터링 시스템", layout="wide")

def get_latest_file(pattern):
    files = glob.glob(pattern)
    return sorted(files)[-1] if files else None

# 데이터 로드
df_a = pd.read_json(get_latest_file('assembly_results_*.json')) if get_latest_file('assembly_results_*.json') else pd.DataFrame()
df_s = pd.read_json(get_latest_file('schedule_results_*.json')) if get_latest_file('schedule_results_*.json') else pd.DataFrame()
df_n = pd.read_json(get_latest_file('news_results_*.json')) if get_latest_file('news_results_*.json') else pd.DataFrame()

# 2. NMC 공식 양식 CSS (색상, 태그, 헤더 디테일 완벽 반영)
STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    .report-wrap { font-family: 'Noto Sans KR', sans-serif; background-color: #F8F9FB; padding: 40px; }
    
    /* 상단 헤더 */
    .header { background: linear-gradient(135deg, #1B3A6B 0%, #2A5298 100%); color: white; padding: 40px 30px; border-radius: 12px; margin-bottom: 30px; }
    .header-top { font-size: 13px; opacity: 0.8; letter-spacing: 1px; margin-bottom: 8px; }
    .header-title { font-size: 30px; font-weight: 700; margin: 0; }
    .header-date { margin-top: 15px; font-size: 15px; opacity: 0.9; }

    /* 요약 카드 */
    .card-box { display: flex; gap: 15px; margin-bottom: 40px; }
    .card { flex: 1; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; border-top: 5px solid #1B3A6B; }
    .card-val { font-size: 32px; font-weight: 700; color: #1B3A6B; margin-bottom: 5px; }
    .card-lbl { font-size: 13px; color: #666; font-weight: 600; }

    /* 섹션 제목 (이미지 속 디테일 반영) */
    .sec-header { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #1B3A6B; padding-bottom: 10px; margin-top: 45px; margin-bottom: 20px; }
    .sec-title-text { font-size: 22px; font-weight: 800; color: #1B3A6B; border-left: 6px solid #1B3A6B; padding-left: 15px; line-height: 1; }
    .time-stamp { font-size: 12px; color: #A0AEC0; margin-left: 12px; font-weight: normal; }
    .sec-meta { font-size: 14px; color: #888; font-weight: 600; }

    /* 아이템 카드 및 포인트 바 */
    .item-card { background: white; padding: 30px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); position: relative; overflow: hidden; }
    .point-bar { position: absolute; left: 0; top: 0; bottom: 0; width: 8px; }
    
    /* 둥근 알약 키워드 태그 */
    .keyword-tag { display: inline-block; background-color: #E9EFF6; color: #1B3A6B; padding: 4px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; margin-right: 8px; margin-bottom: 12px; }
    
    /* 배지 및 텍스트 */
    .badge { padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 700; color: white; vertical-align: middle; margin-right: 8px; }
    .item-title { font-size: 19px; font-weight: 700; color: #111; margin: 12px 0; }
    .meta-box { background: #F1F3F7; padding: 15px; border-radius: 8px; font-size: 14px; color: #4A5568; margin: 15px 0; display: flex; gap: 20px; }
    .summary-box { font-size: 15px; line-height: 1.8; color: #333; text-align: justify; margin-top: 15px; word-break: keep-all; }
    .link-btn { display: inline-block; margin-top: 20px; font-size: 13px; font-weight: 700; color: #1B3A6B; text-decoration: none; border: 1.5px solid #1B3A6B; padding: 6px 15px; border-radius: 5px; }
</style>
"""

st.title("🚑 NMC 정책 모니터링 자동 보고서")

# 3. 항목 선택 UI
selected = {'a': [], 's': [], 'n': []}
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("📋 의안 선택")
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

# 4. 보고서 생성 로직
if st.button("✨ NMC 공식 양식으로 보고서 발행", use_container_width=True):
    total = len(selected['a