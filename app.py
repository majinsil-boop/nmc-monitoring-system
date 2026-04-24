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
        sel_a = [r for i, r in enumerate(asm_raw) if st.checkbox(escape(r.get('bill_name','')[:15]), True, key="a"+str(i))]
    with col2:
        st.subheader("❷ 일정")
        sel_s = [r for i, r in enumerate(sch_raw) if st.checkbox(escape(r.get('title','')[:15]), True, key="s"+str(i))]
    with col3:
        st.subheader("❸ 뉴스")
        sel_n = [r for i, r in enumerate(news_raw) if st.checkbox(escape(r.get('title','')[:15]), True, key="n"+str(i))]

    if st.button("✨ 보고서 발행", use_container_width=True):
        st.session_state.update({"sel_a": sel_a, "sel_s": sel_s, "sel_n": sel_n, "phase": "REPORT"})
        st.rerun()

# [B] 보고서 화면 (디자인 복구 + 1페이지 압축)
else:
    if st.sidebar.button("🔙 다시 선택하기"):
        st.session_state.phase = "SELECT"
        st.rerun()

    today = datetime.now().strftime("%Y-%m-%d")
    
    # 인쇄용 CSS (디자인은 살리고 간격만 조절)
    st.markdown("<style>[data-testid='stHeader'] { display: none; } @media print { header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; } .main { padding: 0 !important; } .report-container { width: 100% !important; padding: 0 !important; } }</style>", unsafe_allow_html=True)

    # 1) 헤더 (이미지 bfc89e 스타일)
    h_style = "background:#1B3A6B; color:#fff; padding:25px 30px; border-radius:12px 12px 0 0; -webkit-print-color-adjust:exact;"
    html = '<div class="report-container" style="background:#fff; font-family:sans-serif; max-width:750px; margin:auto; border:1px solid #eee; padding:20px; border-radius:15px;">'
    html += '<div style="' + h_style + '"><div style="font-size:10px; opacity:0.8; margin-bottom:5px;">응급의료정책팀 모니터링</div><div style="font-size:24px; font-weight:800;">의료정책 모니터링 보고서 (' + today + ')</div></div>'
    
    # 2) 요약 카드 복구 (이미지 bfc89e의 아이콘 포함 디자인)
    html += '<div style="display:flex; gap:12px; padding:20px 0;">'
    card_info = [("📋", "의안", len(st.session_state.sel_a), "#1B3A6B"), ("📅", "일정", len(st.session_state.sel_s), "#28A745"), ("📰", "뉴스", len(st.session_state.sel_n), "#DC3545")]
    for icon, label, val, color in card_info:
        c_style = "flex:1; background:#fff; border-radius:15px; border-top:5px solid " + color + "; padding:15px 5px; text-align:center; box-shadow:0 4px 10px rgba(0,0,0,0.05); -webkit-print-color-adjust:exact;"
        html += '<div style="' + c_style + '"><div style="font-size:20px; margin-bottom:5px;">' + icon + '</div><div style="font-size:28px; font-weight:800; color:' + color + ';">' + str(val) + '</div><div style="font-size:11px; color:#666; font-weight:700;">' + label + '</div></div>'
    html += '</div>'

    # ❶ 의안 (박스 디자인 유지)
    if st.session_state.sel_a:
        html += '<div style="margin-top:15px; font-size:17px; font-weight:800; color:#1B3A6B;">1. 의안 현황</div>'
        for r in st.session_state.sel_a:
            html += '<div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:15px; margin-bottom:10px; border-left:6px solid #3B82F6; -webkit-print-color-adjust:exact;">'
            html += '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"><div style="font-size:14px; font-weight:800;">' + escape(r.get("bill_name","")) + '</div><div style="background:#1B3A6B; color:#fff; padding:2px 10px; border-radius:12px; font-size:10px;">소관위접수</div></div>'
            html += '<div style="font-size:11px; color:#555; line-height:1.5;">' + escape(r.get("summary","")[:160]) + '...</div></div>'

    # ❷ 일정 (심플 박스)
    if st.session_state.sel_s:
        html += '<div style="margin-top:20px; font-size:17px; font-weight:800; color:#1B3A6B;">2. 주요 일정</div>'
        for r in st.session_state.sel_s:
            html += '<div style="background:#fff; border-radius:12px; border:1px solid #E2E8F0; padding:12px 20px; margin-bottom:8px; border-left:6px solid #28A745; display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust:exact;"><div style="font-size:13px; font-weight:700;">' + escape(r.get("title","")) + '</div><div style="font-size:12px; color:#333;">' + escape(r.get("date","")) + '</div></div>'

    # ❸ 뉴스 (배지 색상 복구)
    if st.session_state.sel_n:
        html += '<div style="margin-top:20px; font-size:17px; font-weight:800; color:#1B3A6B;">3. 언론 모니터링</div>'
        for r in st.session_state.sel_n:
            kw = r.get('keyword', '중증응급')
            # 연구원님 스타일의 배지 색상 매핑
            kw_color = {"중증응급":"#800000", "중증외상":"#1B3A6B", "응급의료":"#DC3545", "필수의료":"#E07B00"}.get(kw, "#DC3545")
            html += '<div style="background:#fff; border-radius:12px; border:1px solid #E2E8F0; padding:10px 20px; margin-bottom:8px; border-left:6px solid #DC3545; display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust:exact;">'
            html += '<div style="font-size:13px; font-weight:700;">' + escape(r.get("title","")[:45]) + '</div>'
            html += '<div style="background:'+kw_color+'; color:#fff; padding:3px 12px; border-radius:15px; font-size:10px; font-weight:700;">' + escape(kw) + '</div></div>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    st.success("✅ 디자인이 복구되었습니다. 이제 Ctrl+P로 한 장에 저장하세요!")