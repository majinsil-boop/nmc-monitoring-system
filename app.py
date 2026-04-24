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
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("❶ 의안")
        sel_a = [r for i, r in enumerate(asm_raw) if st.checkbox(f"{r.get('bill_name','')[:15]}", True, key=f"a{i}")]
    with col2:
        st.subheader("❷ 일정")
        sel_s = [r for i, r in enumerate(sch_raw) if st.checkbox(f"{r.get('title','')[:15]}", True, key=f"s{i}")]
    with col3:
        st.subheader("❸ 뉴스")
        sel_n = [r for i, r in enumerate(news_raw) if st.checkbox(f"{r.get('title','')[:15]}", True, key=f"n{i}")]

    if st.button("✨ 보고서 발행", use_container_width=True):
        st.session_state.update({"sel_a": sel_a, "sel_s": sel_s, "sel_n": sel_n, "phase": "REPORT"})
        st.rerun()

# [B] 보고서 화면 (요약표 및 간격 극단적 축소)
else:
    if st.sidebar.button("🔙 다시 선택"):
        st.session_state.phase = "SELECT"
        st.rerun()

    today = datetime.now().strftime("%Y-%m-%d")
    
    st.markdown("""
        <style>
        [data-testid="stHeader"] { display: none; }
        @media print {
            header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; }
            .main { padding: 0 !important; }
            .report-container { width: 100% !important; padding: 5px !important; }
            .item-box { page-break-inside: avoid; margin-bottom: 3px !important; }
        }
        </style>
    """, unsafe_allow_html=True)

    # 1) 헤더 (높이 최소화)
    html = f"""
    <div class="report-container" style="background:#fff; font-family:sans-serif; max-width:700px; margin:auto; border:1px solid #eee; padding:15px;">
        <div style="background:#1B3A6B; color:#fff; padding:15px 20px; border-radius:8px; -webkit-print-color-adjust:exact; display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size:18px; font-weight:800;">의료정책 모니터링 보고서 ({today})</div>
            <div style="font-size:9px; opacity:0.7;">국립중앙의료원</div>
        </div>
        
        <div style="display:flex; gap:8px; padding:10px 0;">
    """
    
    # 2) 요약 카드 (연구원님 요청대로 크기 대폭 축소)
    def mini_card(label, val, color):
        return f"""
        <div style="flex:1; border:1px solid {color}; border-left:5px solid {color}; padding:8px; text-align:center; -webkit-print-color-adjust:exact;">
            <span style="font-size:10px; color:#666;">{label}: </span>
            <span style="font-size:16px; font-weight:800; color:{color};">{val}</span>
        </div>
        """

    html += mini_card("의안", len(st.session_state.sel_a), "#1B3A6B")
    html += mini_card("일정", len(st.session_state.sel_s), "#28A745")
    html += mini_card("뉴스", len(st.session_state.sel_n), "#DC3545")
    html += "</div>"

    # ❶ 의안 (폰트 및 여백 압축)
    if st.session_state.sel_a:
        html += '<div style="margin-top:10px; border-bottom:1px solid #1B3A6B; font-size:13px; font-weight:800; color:#1B3A6B;">1. 의안 현황</div>'
        for r in st.session_state.sel_a:
            html += f'<div class="item-box