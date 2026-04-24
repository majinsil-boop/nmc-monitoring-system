import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 페이지 설정
st.set_page_config(page_title="NMC 보고서", layout="wide")

def _load_data(pattern):
    curr = os.path.dirname(os.path.abspath(__file__))
    f_path = os.path.join(curr, pattern)
    fs = sorted(glob.glob(f_path))
    if not fs: return []
    try:
        with open(fs[-1], encoding="utf-8") as f:
            return json.load(f)
    except: return []

# [안전형] 주소 보정 - 중복 방지 로직 추가
def fix_url(u):
    if not u or str(u).strip() in ["#", ""]: return "#"
    s = str(u).strip()
    if s.lower().startswith("http"): return s
    return "https://" + s

a_r = _load_data("assembly_results_*.json")
s_r = _load_data("schedule_results_*.json")
n_r = _load_data("news_results_*.json")

if "phase" not in st.session_state:
    st.session_state.phase = "SELECT"

if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 보고서 생성기")
    sa, ss, sn = [], [], []

    st.subheader("❶ 의안")
    for i, r in enumerate(a_r):
        lk = fix_url(r.get("link") or r.get("bill_link"))
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.checkbox(f"**{r.get('bill_name','')}**", key=f"ca{i}"): sa.append(r)
        with col2:
            st.link_button("원문보기 🔗", lk) # [공식 버튼 사용]
        st.write("---")

    st.subheader("❷ 일정")
    for i, r in enumerate(s_r):
        lk = fix_url(r.get("link"))
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.checkbox(f"📅 {r.get('title','')}", key=f"cs{i}"): ss.append(r)
        with col2:
            st.link_button("원문보기 🔗", lk)
        st.write("---")

    st.subheader("❸ 뉴스")
    for i, r in enumerate(n_r):
        lk = fix_url(r.get("link") or r.get("url"))
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.checkbox(f"📰 {r.get('title','')}", key=f"cn{i}"): sn.append(r)
        with col2:
            st.link_button("기사보기 🔗", lk)
        st.write("---")

    if st.button("✨ 보고서 발행", use_container_width=True):
        st.session_state.sel_a, st.session_state.sel_s, st.session_state.sel_n = sa, ss, sn
        st.session_state.phase = "REPORT"; st.rerun()

else:
    # [보고서 화면] 여기는 PDF 출력을 위해 기존 HTML 방식을 유지하되 링크만 보정
    t = datetime.now().strftime("%Y-%m-%d")
    st.sidebar.button("🔙 다시 선택", on_click=lambda: st.session_state.update({"phase":"SELECT"}))
    
    html = '<div style="background:#FBFBFB; padding:20px; font-family:sans-serif;">'
    # ... (헤더 생략)
    
    if st.session_state.sel_a:
        html += '<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">❶ 의안 현황</div>'
        for r in st.session_state.sel_a:
            l = fix_url(r.get("link") or r.get("bill_link"))
            html += f'<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #1B3A6B; padding:15px; border-radius:12px; margin-bottom:10px;">'
            html += f'<div style="display:flex; justify-content:space-between; align-items:center;">'
            html += f'<div style="font-size:14px; font-weight:800; color:#1B3A6B;">{escape(str(r.get("bill_name","")))}</div>'
            html += f'<a href="{l}" target="_blank" style="background:#1B3A6B; color:#fff; padding:4px 10px; border-radius:5px; font-size:10px; text-decoration:none;">원문보기 🔗</a></div></div>'
    
    # ... (나머지 섹션도 위 lk 보정 로직과 동일하게 적용)
    st.markdown(html, unsafe_allow_html=True)