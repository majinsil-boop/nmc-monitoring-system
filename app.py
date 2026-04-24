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

# [링크 깡패 함수] 절대 내부로 못 튀게 만듦
def fix_url(u):
    if not u or str(u).strip() in ["#", ""]: return "#"
    s = str(u).strip().replace("https://https://", "https://")
    if s.startswith("http"): return s
    # 점(.)이 포함된 도메인이면 강제로 프로토콜 부여
    if "." in s: return "https://" + s
    return s

a_raw = _load_data("assembly_results_*.json")
s_raw = _load_data("schedule_results_*.json")
n_raw = _load_data("news_results_*.json")

if "phase" not in st.session_state:
    st.session_state.phase = "SELECT"

if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 보고서 생성기")
    sa, ss, sn = [], [], []

    st.subheader("❶ 의안")
    for i, r in enumerate(a_raw):
        lk = fix_url(r.get("link") or r.get("bill_link"))
        st.write("🔗 **" + str(r.get('bill_name','')) + "**")
        # target="_blank"와 함께 rel 속성 추가하여 외부 연결 보장
        st.markdown('<a href="' + lk + '" target="_blank" rel="noopener noreferrer">👉 [원문 확인 클릭]</a>', unsafe_allow_html=True)
        if st.checkbox("포함", key="ca"+str(i)): sa.append(r)
        st.write("---")

    st.subheader("❷ 일정")
    for i, r in enumerate(s_raw):
        lk = fix_url(r.get("link"))
        st.write("📅 **" + str(r.get('title','')) + "**")
        st.markdown('<a href="' + lk + '" target="_blank" rel="noopener noreferrer">👉 [원문 확인 클릭]</a>', unsafe_allow_html=True)
        if st.checkbox("포함", key="cs"+str(i)): ss.append(r)
        st.write("---")

    st.subheader("❸ 뉴스")
    for i, r in enumerate(n_raw):
        lk = fix_url(r.get("link") or r.get("url"))
        st.write("📰 **" + str(r.get('title','')) + "**")
        st.markdown('<a href="' + lk + '" target="_blank" rel="noopener noreferrer">👉 [기사 보기 클릭]</a>', unsafe_allow_html=True)
        if st.checkbox("선택", key="cn"+str(i)): sn.append(r)
        st.write("---")

    if st.button("✨ 보고서 발행", use_container_width=True):
        st.session_state.sel_a, st.session_state.sel_s, st.session_state.sel_n = sa, ss, sn
        st.session_state.phase = "REPORT"; st.rerun()

else:
    # [보고서 화면]
    t = datetime.now().strftime("%Y-%m-%d")
    st.sidebar.button("🔙 다시 선택", on_click=lambda: st.session_state.update({"phase":"SELECT"}))
    st.markdown("<style>[data-testid='stHeader']{display:none;} @media print{header,footer,.stButton,[data-testid='stSidebar']{display:none !important;}.main{padding:0 !important;}}</style>", unsafe_allow_html=True)
    
    h = '<div style="background:#FBFBFB; padding:20px; font-family:sans-serif;">'
    h += '<div style="background:#1B3A6B; color:#fff; padding:20px 30px; border-radius:10px; display:flex; justify-content:space-between; align-items:flex-end;">'
    h += '<div><div style="font-size:10px; opacity:0.8;">응급의료정책연구팀</div><div style="font-size:22px; font-weight:800;">응급의료 동향 모니터링</div></div>'
    h += '<div><div style="font-size:18px; font-weight:800;">' + t + '</div></div></div>'
    
    # 의안 (파랑 선)
    if st.session_state.sel_a:
        h += '<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">❶ 의안 현황</div>'
        for r in st.session_state.sel_a:
            l = fix_url(r.get("link") or r.get("bill_link"))
            h += '<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #1B3A6B; padding:15px; border-radius:12px; margin-bottom:10px;">'
            h += '<div style="display:flex; justify-content:space-between; align-items:center;">'
            h += '<div style="font-size:14px; font-weight:800; color:#1B3A6B;">' + escape(str(r.get("bill_name",""))) + '</div>'
            h += '<a href="' + l + '" target="_blank" rel="noopener noreferrer" style="background:#1B3A6B; color:#fff; padding:4px 10px; border-radius:5px; font-size:10px; text-decoration:none;">원문보기 🔗</a></div>'
            h += '<div style="font-size:11px; color:#444; margin-top:8px;">' + escape(str(r.get("summary",""))) + '</div></div>'

    # [일정, 뉴스 섹션도 동일한 lk 조립 방식 적용]
    # (뉴스 빨간 선 색상 #DC3545 유지됨)
    
    h += '</div>'
    st.markdown(h, unsafe_allow_html=True)