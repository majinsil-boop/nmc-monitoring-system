import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 설정 및 데이터 로드
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _load_data(pattern):
    files = sorted(glob.glob(os.path.join(os.getcwd(), pattern)))
    if not files: return []
    try:
        with open(files[-1], encoding="utf-8") as f:
            return json.load(f)
    except: return []

asm_raw = _load_data("assembly_results_*.json")
sch_raw = _load_data("schedule_results_*.json")
news_raw = _load_data("news_results_*.json")

if "phase" not in st.session_state:
    st.session_state.phase = "SELECT"

# [A] 선택 화면 - 링크 클릭 시 새 탭에서 열림
if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")
    
    # ❶ 의안 현황
    st.write("---")
    st.subheader("❶ 의안 현황")
    sel_a = []
    for i, r in enumerate(asm_raw):
        link = r.get('link', r.get('bill_link', '#'))
        col_t, col_l = st.columns([0.8, 0.2])
        with col_t:
            is_checked = st.checkbox(f"[{r.get('status','접수')}] {r.get('bill_name','')}", False, key=f"a{i}")
        with col_l:
            if link != '#':
                st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none;">🔗 원문보기</a>', unsafe_allow_html=True)
        if is_checked: sel_a.append(r)
        st.caption(f"내용 요약: {r.get('summary','')}...")

    # ❷ 주요 일정
    st.write("---")
    st.subheader("❷ 주요 일정")
    sel_s = []
    for i, r in enumerate(sch_raw):
        link = r.get('link', '#')
        col_t, col_l = st.columns([0.8, 0.2])
        with col_t:
            is_checked = st.checkbox(f"📅 [{r.get('date','')}] {r.get('title','')}", False, key=f"s{i}")
        with col_l:
            if link != '#':
                st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none;">🔗 원문보기</a>', unsafe_allow_html=True)
        if is_checked: sel_s.append(r)

    # ❸ 언론 모니터링
    st.write("---")
    st.subheader("❸ 언론 모니터링")
    sel_n = []
    for i, r in enumerate(news_raw):
        link = r.get('link', r.get('url', '#'))
        col_t, col_l = st.columns([0.8, 0.2])
        with col_t:
            is_checked = st.checkbox(f"📰 [{r.get('source','')}] {r.get('title','')} ({r.get('keyword','뉴스')})", False, key=f"n{i}")
        with col_l:
            if link != '#':
                st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none;">🔗 기사보기</a>', unsafe_allow_html=True)
        if is_checked: sel_n.append(r)

    st.write("---")
    if st.button("✨ 선택 완료 및 보고서 발행", use_container_width=True):
        st.session_state.update({"sel_a": sel_a, "sel_s": sel_s, "sel_n": sel_n, "phase": "REPORT"})
        st.rerun()

# [B] 보고서 화면 (bfb639 디자인 대응)
else:
    if st.sidebar.button("🔙 다시 선택하기"):
        st.session_state.phase = "SELECT"
        st.rerun()

    today = datetime.now().strftime("%Y-%m-%d")
    st.markdown("<style>[data-testid='stHeader'] { display: none; } @media print { header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; } .main { padding: 0 !important; } }</style>", unsafe_allow_html=True)

    html = '<div style="background:#FBFBFB; padding:30px; font-family:sans-serif;">'
    html += '<div style="background:#1B3A6B; color:#fff; padding:20px 30px; display:flex; justify-content:space-between; align-items:flex-end; -webkit-print-color-adjust:exact;">'
    html += '<div><div style="font-size:10px; opacity:0.8;">응급의료정책연구팀</div><div style="font-size:22px; font-weight:800;">응급의료 동향 모니터링</div></div>'
    html += '<div style="text-align:right;"><div style="font-size:18px; font-weight:800;">' + today + '</div></div></div>'

    html += '<div style="display:flex; gap:10px; padding:15px 0;">'
    for icon, label, val, bg in [("📋","의안",len(st.session_state.sel_a),"#EBF1F9"), ("📅","일정",len(st.session_state.sel_s),"#E8F5E9"), ("📰","뉴스",len(st.session_state.sel_n),"#FDECEA"), ("📊","전체",len(st.session_state.sel_a)+len(st.session_state.sel_s)+len(st.session_state.sel_n),"#F3F4F6")]:
        html += '<div style="flex:1; background:'+bg+'; border-radius:10px; padding:15px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.05); -webkit-print-color-adjust:exact;"><div style="font-size:18px;">'+icon+'</div><div style="font-size:28px; font-weight:800; color:#1B3A6B;">'+str(val)+'</div><div style="font-size:11px; font-weight:700; color:#1B3A6B;">'+label+'</div></div>'
    html += '</div>'

    if st.session_state.sel_a:
        html += '<div style="margin:20px 0 10px; font-size:18px; font-weight:800; color:#1B3A6B;">❶ 의안 현황</div>'
        for r in st.session_state.sel_a:
            html += '<div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:20px; margin-bottom:15px; -webkit-print-color-adjust:exact;"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"><div style="font-size:15px; font-weight:800; color:#1B3A6B;">' + escape(r.get('bill_name','')) + '</div><div style="background:#1B3A6B; color:#fff; padding:3px 12px; border-radius:15px; font-size:11px;">접수</div></div><div style="background:#FFF9E6; border:1px solid #FFD966; color:#856404; padding:5px 12px; border-radius:5px; font-size:12px; font-weight:700; margin-bottom:12px; display:inline-block;">입법예고 진행중</div><div style="font-size:12px; color:#444; line-height:1.6;">' + escape(r.get('summary','')) + '</div></div>'

    if st.session_state.sel_s:
        html += '<div style="margin:30px 0 10px; font-size:18px; font-weight:800; color:#1B3A6B;">❷ 주요 일정</div>'
        for r in st.session_state.sel_s:
            html += '<div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:15px 20px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; border-left:6px solid #28A745; -webkit-print-color-adjust:exact;"><div><div style="font-size:14px; font-weight:800;">' + escape(r.get('title','')) + '</div><div style="margin-top:5px;"><span style="background:#E8F5E9; color:#1B5E20; padding:2px 8px; border-radius:5px; font-size:11px; font-weight:700;">토론회</span></div></div><div style="font-size:13px; font-weight:800; color:#333;">' + escape(r.get('date','')) + '</div></div>'

    if st.session_state.sel_n:
        html += '<div style="margin:30px 0 10px; font-size:18px; font-weight:800; color:#1B3A6B;">❸ 언론 모니터링</div>'
        for r in st.session_state.sel_n:
            kw = r.get('keyword','응급의료'); c_hex = {"중증응급":"#800000", "중증외상":"#6F42C1", "상급종합병원":"#A52A2A"}.get(kw, "#DC3545")
            html += '<div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:15px 20px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust:exact;"><div><div style="font-size:14px; font-weight:800; color:#1B3A6B;">' + escape(r.get('title','')) + '</div><div style="font-size:11px; color:#777; margin-top:5px;">' + escape(r.get('source','')) + ' | ' + escape(r.get('date','')) + '</div></div><div style="background:'+c_hex+'; color:#fff; padding:3px 12px; border-radius:15px; font-size:11px; font-weight:700;">' + escape(kw) + '</div></div>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)