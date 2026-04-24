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
    st.info("원문 링크를 클릭해 내용을 확인하신 후, 포함할 항목을 체크해 주세요.")
    
    # 데이터 수집용 임시 리스트
    final_a, final_s, final_n = [], [], []

    # ❶ 의안 현황
    st.write("---")
    st.subheader("❶ 의안 현황")
    for i, r in enumerate(asm_raw):
        link = r.get('link', r.get('bill_link', '#'))
        with st.expander(f"[{r.get('status','접수')}] {r.get('bill_name','')}", expanded=False):
            if link != '#': st.markdown(f"🔗 [의안 원문 열기]({link})")
            st.write(f"**요약:** {r.get('summary','')}")
            # 체크되면 임시 리스트에 추가
            if st.checkbox("이 의안 선택", False, key=f"check_a{i}"):
                final_a.append(r)
    
    # ❷ 주요 일정
    st.write("---")
    st.subheader("❷ 주요 일정")
    for i, r in enumerate(sch_raw):
        link = r.get('link', '#')
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            if st.checkbox(f"📅 [{r.get('date','')}] {r.get('title','')}", False, key=f"check_s{i}"):
                final_s.append(r)
        with col2:
            if link != '#': st.markdown(f"[🔗 원문]({link})")
    
    # ❸ 언론 모니터링
    st.write("---")
    st.subheader("❸ 언론 모니터링")
    for i, r in enumerate(news_raw):
        link = r.get('link', r.get('url', '#'))
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            if st.checkbox(f"📰 [{r.get('source','')}] {r.get('title','')} ({r.get('keyword','뉴스')})", False, key=f"check_n{i}"):
                final_n.append(r)
        with col2:
            if link != '#': st.markdown(f"[🔗 기사]({link})")

    st.write("---")
    # [핵심] 버튼 클릭 시 세션에 데이터를 확실히 저장
    if st.button("✨ 선택 완료 및 보고서 발행", use_container_width=True):
        st.session_state.sel_a = final_a
        st.session_state.sel_s = final_s
        st.session_state.sel_n = final_n
        st.session_state.phase = "REPORT"
        st.rerun()

# [B] 보고서 화면 (이미지 bfb639 디자인 대응)
else:
    if st.sidebar.button("🔙 다시 선택하기"):
        st.session_state.phase = "SELECT"
        st.rerun()

    today = datetime.now().strftime("%Y-%m-%d")
    st.markdown("<style>[data-testid='stHeader'] { display: none; } @media print { header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; } .main { padding: 0 !important; } }</style>", unsafe_allow_html=True)

    header = f"""
    <div style="background:#1B3A6B; color:#fff; padding:20px 30px; display:flex; justify-content:space-between; align-items:flex-end; -webkit-print-color-adjust:exact;">
        <div><div style="font-size:10px; opacity:0.8;">국립중앙의료원 중앙응급의료센터</div><div style="font-size:22px; font-weight:800;">의료정책 모니터링 보고서</div></div>
        <div style="text-align:right;"><div style="font-size:18px; font-weight:800;">{today}</div></div>
    </div>
    """

    def c(icon, label, val, bg):
        return f'<div style="flex:1; background:{bg}; border-radius:10px; padding:15px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.05); -webkit-print-color-adjust:exact;"><div style="font-size:18px;">{icon}</div><div style="font-size:28px; font-weight:800; color:#1B3A6B;">{val}</div><div style="font-size:11px; font-weight:700; color:#1B3A6B;">{label}</div></div>'

    cards = f"""
    <div style="display:flex; gap:10px; padding:15px 0;">
        {c("📋","계류 의안",len(st.session_state.sel_a),"#EBF1F9")}
        {c("📅","예정 일정",len(st.session_state.sel_s),"#E8F5E9")}
        {c("📰","언론 기사",len(st.session_state.sel_n),"#FDECEA")}
        {c("📊","전체",len(st.session_state.sel_a)+len(st.session_state.sel_s)+len(st.session_state.sel_n),"#F3F4F6")}
    </div>
    """

    body = ""
    if st.session_state.sel_a:
        body += '<div style="margin:20px 0 10px; font-size:18px; font-weight:800; color:#1B3A6B;">❶ 의안 현황</div>'
        for r in st.session_state.sel_a:
            body += f"""<div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:20px; margin-bottom:15px; -webkit-print-color-adjust:exact;"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"><div style="font-size:15px; font-weight:800; color:#1B3A6B;">{escape(r.get('bill_name',''))}</div><div style="background:#1B3A6B; color:#fff; padding:3px 12px; border-radius:15px; font-size:11px;">{escape(r.get('status','접수'))}</div></div><div style="background:#FFF9E6; border:1px solid #FFD966; color:#856404; padding:5px 12px; border-radius:5px; font-size:12px; font-weight:700; margin-bottom:12px; display:inline-block;">입법예고 진행중</div><div style="font-size:12px; color:#444; line-height:1.6;">{escape(r.get('summary',''))}</div></div>"""

    if st.session_state.sel_s:
        body += '<div style="margin:30px 0 10px; font-size:18px; font-weight:800; color:#1B3A6B;">❷ 주요 일정</div>'
        for r in st.session_state.sel_s:
            body += f"""<div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:15px 20px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; border-left:6px solid #28A745; -webkit-print-color-adjust:exact;"><div><div style="font-size:14px; font-weight:800;">{escape(r.get('title',''))}</div><div style="margin-top:5px;"><span style="background:#E8F5E9; color:#1B5E20; padding:2px 8px; border-radius:5px; font-size:11px; font-weight:700;">토론회</span></div></div><div style="font-size:13px; font-weight:800; color:#333;">{escape(r.get('date',''))}</div></div>"""

    if st.session_state.sel_n:
        body += '<div style="margin:30px 0 10px; font-size:18px; font-weight:800; color:#1B3A6B;">❸ 언론 모니터링</div>'
        for r in st.session_state.sel_n:
            kw = r.get('keyword','응급의료'); c_hex = {"중증응급":"#800000", "중증외상":"#6F42C1", "상급종합병원":"#A52A2A"}.get(kw, "#DC3545")
            body += f"""<div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:15px 20px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust:exact;"><div><div style="font-size:14px; font-weight:800; color:#1B3A6B;">{escape(r.get('title',''))}</div><div style="font-size:11px; color:#777; margin-top:5px;">{escape(r.get('source',''))} | {escape(r.get('date',''))}</div></div><div style="background:{c_hex}; color:#fff; padding:3px 12px; border-radius:15px; font-size:11px; font-weight:700;">{escape(kw)}</div></div>"""

    st.markdown(f'<div style="background:#FBFBFB; padding:30px; font-family:sans-serif;">{header}{cards}{body}</div>', unsafe_allow_html=True)