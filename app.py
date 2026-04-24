import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

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

a_raw = _load_data("assembly_results_*.json")
s_raw = _load_data("schedule_results_*.json")
n_raw = _load_data("news_results_*.json")

if "phase" not in st.session_state:
    st.session_state.phase = "SELECT"

if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 보고서 생성기")
    sa, ss, sn = [], [], []

    # ❶ 의안 - 뉴스랑 똑같은 [텍스트](링크) 문법으로 고정
    st.subheader("❶ 의안")
    for i, r in enumerate(a_raw):
        lk = str(r.get("link") or r.get("bill_link") or "#").strip()
        if "." in lk and not lk.startswith("http"): lk = "https://" + lk
        st.markdown(f"🔗 **{r.get('bill_name','')}**")
        st.markdown(f"[👉 여기를 클릭해서 국회 원문 보기]({lk})")
        if st.checkbox("포함", key=f"ca{i}"): sa.append(r)
        st.write("---")

    # ❷ 일정
    st.subheader("❷ 일정")
    for i, r in enumerate(s_raw):
        lk = str(r.get("link", "#")).strip()
        if "." in lk and not lk.startswith("http"): lk = "https://" + lk
        st.markdown(f"📅 **{r.get('title','')}**")
        st.markdown(f"[👉 여기를 클릭해서 상세 일정 보기]({lk})")
        if st.checkbox("포함", key=f"cs{i}"): ss.append(r)
        st.write("---")

    # ❸ 뉴스 (이미 성공한 섹션)
    st.subheader("❸ 뉴스")
    for i, r in enumerate(n_raw):
        lk = str(r.get("link") or r.get("url") or "#").strip()
        if "." in lk and not lk.startswith("http"): lk = "https://" + lk
        st.markdown(f"📰 **{r.get('title','')}**")
        st.markdown(f"[👉 여기를 클릭해서 뉴스 기사 보기]({lk})")
        if st.checkbox("선택", key=f"cn{i}"): sn.append(r)
        st.write("---")

    if st.button("✨ 보고서 발행"):
        st.session_state.sel_a, st.session_state.sel_s, st.session_state.sel_n = sa, ss, sn
        st.session_state.phase = "REPORT"; st.rerun()

else:
    # 보고서 화면도 최대한 단순화해서 '깡' 링크로 구성
    t = datetime.now().strftime("%Y-%m-%d")
    st.sidebar.button("🔙 다시 선택", on_click=lambda: st.session_state.update({"phase":"SELECT"}))
    
    st.markdown(f"# 🚑 응급의료 동향 보고서 ({t})")
    
    if st.session_state.sel_a:
        st.subheader("❶ 의안 현황")
        for r in st.session_state.sel_a:
            l = str(r.get("link") or r.get("bill_link") or "#").strip()
            if "." in l and not l.startswith("http"): l = "https://" + l
            st.markdown(f"**{r.get('bill_name','')}**")
            st.markdown(f"[원문 링크 바로가기]({l})")
            st.caption(r.get("summary",""))

    if st.session_state.sel_s:
        st.subheader("❷ 주요 일정")
        for r in st.session_state.sel_s:
            l = str(r.get("link", "#")).strip()
            if "." in l and not l.startswith("http"): l = "https://" + l
            st.markdown(f"📅 {r.get('date','')} - **{r.get('title','')}**")
            st.markdown(f"[일정 링크 바로가기]({l})")

    if st.session_state.sel_n:
        st.subheader("❸ 언론 모니터링")
        for r in st.session_state.sel_n:
            l = str(r.get("link") or r.get("url") or "#").strip()
            if "." in l and not l.startswith("http"): l = "https://" + l
            st.markdown(f"📰 **{r.get('title','')}** ({r.get('source','')})")
            st.markdown(f"[뉴스 기사 바로가기]({l})")