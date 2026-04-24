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

# [A] 선택 화면
if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")
    st.info("발행할 항목을 체크한 뒤 하단의 버튼을 눌러주세요.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("❶ 의안")
        sel_a = [r for i, r in enumerate(asm_raw) if st.checkbox(escape(r.get('bill_name','')[:15]), True, key="a"+str(i))]
    with col2:
        st.subheader("❷ 일정")
        sel_s = [r for i, r in enumerate(sch_raw) if st.checkbox(escape(r.get('title','')[:15]), True, key="s"+str(i))]
    with col3:
        st.subheader("❸ 뉴스")
        sel_n = [r for i, r in enumerate(news_raw) if st.checkbox(escape(r.get('title','')[:15]), True, key="n"+str(i))]

    if st.button("✨ 보고서 발행 (1페이지 최적화)", use_container_width=True):
        st.session_state.update({"sel_a": sel_a, "sel_s": sel_s, "sel_n": sel_n, "phase": "REPORT"})
        st.rerun()

# [B] 보고서 화면 (요약표 축소 및 간격 압축)
else:
    if st.sidebar.button("🔙 다시 선택하기"):
        st.session_state.phase = "SELECT"
        st.rerun()

    today = datetime.now().strftime("%Y-%m-%d")
    
    # 인쇄용 CSS (UI 제거)
    st.markdown("<style>[data-testid='stHeader'] { display: none; } @media print { header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; } .main { padding: 0 !important; } }</style>", unsafe_allow_html=True)

    # 1) 전체 컨테이너 및 헤더
    html = '<div style="background:#fff; font-family:sans-serif; max-width:700px; margin:auto; border:1px solid #eee; padding:15px;">'
    html += '<div style="background:#1B3A6B; color:#fff; padding:15px 20px; border-radius:8px; display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust:exact;">'
    html += '<div style="font-size:18px; font-weight:800;">의료정책 모니터링 보고서 (' + today + ')</div>'
    html += '<div style="font-size:9px; opacity:0.7;">국립중앙의료원</div></div>'
    
    # 2) 요약 미니 바 (크기 대폭 축소)
    html += '<div style="display:flex; gap:8px; padding:10px 0;">'
    summary_items = [("의안", len(st.session_state.sel_a), "#1B3A6B"), ("일정", len(st.session_state.sel_s), "#28A745"), ("뉴스", len(st.session_state.sel_n), "#DC3545")]
    for label, val, color in summary_items:
        c_style = "flex:1; border:1px solid " + color + "; border-left:5px solid " + color + "; padding:8px; text-align:center; -webkit-print-color-adjust:exact;"
        html += '<div style="' + c_style + '"><span style="font-size:10px; color:#666;">' + label + ': </span>'
        html += '<span style="font-size:16px; font-weight:800; color:' + color + ';">' + str(val) + '</span></div>'
    html += '</div>'

    # ❶ 의안 현황
    if st.session_state.sel_a:
        html += '<div style="margin-top:10px; border-bottom:1px solid #1B3A6B; font-size:13px; font-weight:800; color:#1B3A6B;">1. 의안 현황</div>'
        for r in st.session_state.sel_a:
            html += '<div style="padding:4px 0; border-bottom:1px solid #f9f9f9;">'
            html += '<div style="font-size:11px; font-weight:700;">• ' + escape(r.get("bill_name","")) + '</div>'
            html += '<div style="font-size:9.5px; color:#555; line-height:1.3;">' + escape(r.get("summary","")[:140]) + '...</div></div>'

    # ❷ 주요 일정
    if st.session_state.sel_s:
        html += '<div style="margin-top:15px; border-bottom:1px solid #28A745; font-size:13px; font-weight:800; color:#28A745;">2. 주요 일정</div>'
        for r in st.session_state.sel_s:
            html += '<div style="font-size:10.5px; padding:2px 0;">• ' + escape(r.get("title","")) + ' '
            html += '<span style="color:#666; font-size:9px;">(' + escape(r.get("date","")) + ')</span></div>'

    # ❸ 언론 모니터링
    if st.session_state.sel_n:
        html += '<div style="margin-top:15px; border-bottom:1px solid #DC3545; font-size:13px; font-weight:800; color:#DC3545;">3. 언론 모니터링</div>'
        for r in st.session_state.sel_n:
            html += '<div style="font-size:10.5px; padding:2px 0;">• ' + escape(r.get("title","")[:48]) + ' '
            html += '<span style="color:#DC3545; font-size:9px; font-weight:700;">[' + escape(r.get("keyword","뉴스")) + ']</span></div>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    st.success("✅ 보고서 생성 완료! Ctrl+P를 눌러 한 장에 저장하세요.")