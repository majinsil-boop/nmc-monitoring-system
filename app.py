import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 설정 및 데이터 로드
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _load_data(pattern):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files = sorted(glob.glob(os.path.join(current_dir, pattern)))
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

# [A] 선택 화면
if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")
    st.markdown("#### **발행할 항목을 선택해 주세요.**")
    
    sel_a, sel_s, sel_n = [], [], []

    # ❶ 의안 현황
    st.subheader("❶ 의안 현황")
    for i, r in enumerate(asm_raw):
        link = r.get('link', r.get('bill_link', '#'))
        st.markdown(f"**{r.get('bill_name','')}** <a href='{link}' target='_blank'>🔗 [원문보기]</a>", unsafe_allow_html=True)
        if st.checkbox("이 의안 포함", key=f"ca_{i}"):
            sel_a.append(r)
        st.caption(f"📝 요약: {r.get('summary', '요약 없음')}")
        st.write("")

    # ❷ 주요 일정
    st.write("---")
    st.subheader("❷ 주요 일정")
    for i, r in enumerate(sch_raw):
        link = r.get('link', '#')
        st.markdown(f"📅 [{r.get('date','')}] **{r.get('title','')}** <a href='{link}' target='_blank'>🔗 [원문보기]</a>", unsafe_allow_html=True)
        if st.checkbox("이 일정 포함", key=f"cs_{i}"):
            sel_s.append(r)

    # ❸ 언론 모니터링
    st.write("---")
    st.subheader("❸ 언론 모니터링")
    for i, r in enumerate(news_raw):
        link = r.get('link', r.get('url', '#'))
        st.markdown(f"📰 [{r.get('source','')}] **{r.get('title','')}** <a href='{link}' target='_blank'>🔗 [기사보기]</a>", unsafe_allow_html=True)
        if st.checkbox("이 뉴스 포함", key=f"cn_{i}"):
            sel_n.append(r)

    if st.button("✨ 보고서 발행", use_container_width=True):
        st.session_state.sel_a, st.session_state.sel_s, st.session_state.sel_n = sel_a, sel_s, sel_n
        st.session_state.phase = "REPORT"
        st.rerun()

# [B] 보고서 화면 (HTML 코드를 끊어서 작성하여 SyntaxError 방지)
else:
    today = datetime.now().strftime("%Y-%m-%d")
    st.sidebar.button("🔙 다시 선택하기", on_click=lambda: st.session_state.update({"phase": "SELECT"}))
    
    st.markdown("<style>[data-testid='stHeader'] { display: none; } @media print { header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; } .main { padding: 0 !important; } .report-container { transform: scale(0.96); transform-origin: top center; } }</style>", unsafe_allow_html=True)

    html = '<div class="report-container" style="background:#FBFBFB; padding:20px; font-family:sans-serif;">'
    
    # 헤더
    html += f'<div style="background:#1B3A6B; color:#fff; padding:20px 30px; display:flex; justify-content:space-between; align-items:flex-end; -webkit-print-color-adjust:exact; border-radius:10px;">'
    html += f'<div><div style="font-size:10px; opacity:0.8;">응급의료정책연구팀</div><div style="font-size:22px; font-weight:800;">응급의료 동향 모니터링</div></div>'
    html += f'<div style="text-align:right;"><div style="font-size:18px; font-weight:800;">{today}</div></div></div>'

    # 요약 카드
    html += '<div style="display:flex; gap:10px; padding:15px 0;">'
    for icon, label, val, bg in [("📋","의안",len(st.session_state.sel_a),"#EBF1F9"), ("📅","일정",len(st.session_state.sel_s),"#E8F5E9"), ("📰","뉴스",len(st.session_state.sel_n),"#FDECEA"), ("📊","전체",len(st.session_state.sel_a)+len(st.session_state.sel_s)+len(st.session_state.sel_n),"#F3F4F6")]:
        html += f'<div style="flex:1; background:{bg}; border-radius:10px; padding:12px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:5px; -webkit-print-color-adjust:exact;">'
        html += f'<div style="font-size:18px;">{icon}</div><div style="font-size:11px; font-weight:700;">{label}</div><div style="font-size:24px; font-