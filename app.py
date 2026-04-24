import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="NMC 응급의료 모니터링", page_icon="🚑", layout="wide")
st.title("🚑 응급의료 정책 모니터링 대시보드")

# 파일들을 자동으로 찾아주는 함수
def get_latest_file(pattern):
    files = glob.glob(pattern)
    return max(files, key=os.path.getctime) if files else None

# 1. 탭 생성 (순서 변경: 국회 -> 일정 -> 뉴스)
tab1, tab2, tab3 = st.tabs(["🏛️ 국회 의안", "📅 주요 일정", "📰 뉴스 동향"])

# --- 탭 1: 국회 의안 ---
with tab1:
    latest_assembly = get_latest_file('assembly_results_*.json')
    if latest_assembly:
        st.success(f"✅ 최신 파일 반영: {latest_assembly}")
        df = pd.read_json(latest_assembly)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error("국회 데이터 파일을 찾을 수 없습니다.")

# --- 탭 2: 주요 일정 ---
with tab2:
    latest_schedule = get_latest_file('schedule_results_*.json')
    if latest_schedule:
        st.success(f"✅ 최신 파일 반영: {latest_schedule}")
        df = pd.read_json(latest_schedule)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error("일정 데이터 파일을 찾을 수 없습니다.")

# --- 탭 3: 뉴스 동향 ---
with tab3:
    latest_news = get_latest_file('news_results_*.json')
    if latest_news:
        st.success(f"✅ 최신 파일 반영: {latest_news}")
        df = pd.read_json(latest_news)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error("뉴스 데이터 파일을 찾을 수 없습니다.")