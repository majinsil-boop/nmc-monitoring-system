import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="NMC 응급의료 모니터링", page_icon="🚑", layout="wide")
st.title("🚑 응급의료 정책 모니터링 대시보드")

# [수정된 함수] 파일 이름의 숫자 순서대로 정렬하여 진짜 최신 파일을 찾습니다.
def get_latest_file(pattern):
    files = glob.glob(pattern)
    if not files:
        return None
    # 파일 이름을 글자순(날짜순)으로 정렬하여 마지막 파일을 가져옵니다.
    files.sort() 
    return files[-1]

# 1. 탭 생성
tab1, tab2, tab3 = st.tabs(["🏛️ 국회 의안", "📅 주요 일정", "📰 뉴스 동향"])

# --- 탭 1: 국회 의안 ---
with tab1:
    latest_assembly = get_latest_file('assembly_results_*.json')
    if latest_assembly:
        st.success(f"✅ 데이터 반영: {latest_assembly}")
        df = pd.read_json(latest_assembly)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error("국회 데이터 파일을 찾을 수 없습니다.")

# --- 탭 2: 주요 일정 ---
with tab2:
    latest_schedule = get_latest_file('schedule_results_*.json')
    if latest_schedule:
        st.success(f"✅ 데이터 반영: {latest_schedule}")
        df = pd.read_json(latest_schedule)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error("일정 데이터 파일을 찾을 수 없습니다.")

# --- 탭 3: 뉴스 동향 ---
with tab3:
    latest_news = get_latest_file('news_results_*.json')
    if latest_news:
        st.success(f"✅ 데이터 반영: {latest_news}")
        df = pd.read_json(latest_news)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error("뉴스 데이터 파일을 찾을 수 없습니다.")