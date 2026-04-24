import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

st.set_page_config(page_title="NMC 보고서", layout="wide")

def _load_data(pattern):
    c = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(c, pattern)
    fs = sorted(glob.glob(p))
    if not fs: return []
    try:
        with open(fs[-1], encoding="utf-8") as f:
            return json.load(f)
    except: return []

# [핵심] 외부 링크 강제 고정 함수
def fix_url(u):
    if not u: return "#"
    s = str(u).strip()
    if s.startswith("http"): return s
    # 도메인 형태면 무조건 https:// 강제 삽입
    if "." in s: return "https://" + s
    return "#"

a_r = _load_data("assembly_results_*.json")
s_r = _load_data("schedule_results_*.json")
n_r = _load_data("news_results_*.json")

if "phase" not in st.session_state:
    st.session_state.phase = "SELECT"

if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 보고서 생성기")
    sa, ss, sn = [], [], []
    st.subheader("❶ 의안")
    for i, r in enumerate(a_r):
        lk = fix_url(r.get("link") or r.get("bill_link"))
        st.write(f"**{r.get('bill_name','')}**")
        st.markdown(f'<a href="{lk}" target="_blank">🔗 [원문보기]</a>', unsafe_allow_html=True)
        if st.checkbox("선택", key=f"ca{i}"): sa.append(r)
        st.write("---")
    st.subheader("❷ 일정")
    for i, r in enumerate(s_r):
        lk = fix_url(r.get("link"))
        st.write(f"📅 {r.get('title','')}")
        st.markdown(f'<a href="{lk}" target="_blank">🔗 [원문보기]</a>', unsafe_allow_html=True)
        if st.checkbox("선택", key=f"cs{i}"): ss.append(r)
        st.write("---")
    st.subheader("❸ 뉴스")
    for i, r in enumerate(n_r):
        lk = fix_url(r.get("link") or r.get("url"))
        st.write(f"📰 {r.get('title','')}")
        st.markdown(f'<a href="{lk}" target="_blank">🔗 [기사보기]</a>', unsafe_allow_html=True)
        if st.checkbox("선택", key=f"cn{i}"): sn.append(r)
        st.write("---")
    if st.button("✨ 보고서 발행"):
        st.session_state.sel_a, st.session_state.sel_s, st.session_state.sel_n = sa, ss, sn
        st.session_state.phase = "REPORT"; st.rerun()

else:
    t = datetime.now().strftime("%Y-%m-%d")
    st.sidebar.button("🔙 다시 선택", on_click=lambda: st.session_state.update({"phase":"SELECT"}))
    st.markdown("<style>[data-testid='stHeader'] {display:none;} @media print {header, footer, .stButton, [data-testid='stSidebar'] {display:none !important;} .main {padding:0 !important;}}</style>", unsafe_allow_html=True)
    h = '<div style="background:#FBFBFB; padding:20px; font-family:sans-serif;">'
    # 헤더
    h += '<div style="background:#1B3A6B; color:#fff; padding:20px 30px; display:flex; justify-content:space-between; align-items:flex-end; -webkit-print-color-adjust:exact; border-radius:10px;">'
    h += '<div><div style="font-size:10px; opacity:0.8;">응급의료정책연구팀</div><div style="font-size:22px; font-weight:800;">동향 모니터링</div></div>'
    h += f'<div style="text-align:right;"><div style="font-size:18px; font-weight:800;">{t}</div></div></div>'
    
    # 의안 섹션
    if st.session_state.sel_a:
        h += '<div style="margin:15px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">❶ 의안 현황</div>'
        for r in st.session_state.sel_a:
            l = fix_url(r.get("link") or r.get("bill_link"))
            h += '<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #1B3A6B; padding:15px; border-radius:12px; margin-bottom:10px; -webkit-print-color-adjust:exact;">'
            h += '<div style="display:flex; justify-content:space-between; align-items:center;">'
            h += '<div style="font-size:14px; font-weight:800; color:#1B3A6B;">' + escape(r.get("bill_name","")) + '</div>'
            h += '<a href="' + l + '" target="_blank" style="background:#1B3A6B; color:#fff; padding:3px 10px; border-radius:5px; font-size:10px; text-decoration:none;">원문 🔗</a></div>'
            h += '<div style="font-size:11px; color:#444; margin-top:8px;">' + escape(r.get("summary","")) + '</div></div>'

    # 일정 섹션
    if st.session_state.sel_s:
        h += '<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">❷ 주요 일정</div>'
        for r in st.session_state.sel_s:
            l = fix_url(r.get("link"))
            h += '<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #28A745; padding:12px 15px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust:exact;">'
            h += '<div><div style="font-size:13px; font-weight:800; color:#333;">' + escape(r.get("title","")) + '</div></div>'
            h += '<div style="text-align:right;"><div style="font-size:12px; font-weight:800;">' + escape(r.get("date","")) + '</div>'
            h += '<a href="' + l + '" target="_blank" style="background:#28A745; color:#fff; padding:2px 8px; border-radius:4px; font-size:10px; text-decoration:none;">보기 🔗</a></div></div>'

    # 뉴스 섹션 (왼쪽 선 빨간색 고정)
    if st.session_state.sel_n:
        h += '<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">❸ 언론 모니터링</div>'
        for r in st.session_state.sel_n:
            l = fix_url(r.get("link") or r.get("url"))
            kw = r.get("keyword", "응급의료")
            c = {"중증응급":"#800000", "중증외상":"#6F42C1"}.get(kw, "#DC3545")
            h += '<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #DC3545; padding:12px 15px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust:exact;">'
            h += '<div><div style="font-size:13px; font-weight:800; color:#1B3A6B;">' + escape(r.get("title","")) + '</div>'
            h += '<div style="font-size:10px; color:#777;">' + escape(r.get("source","")) + ' | ' + escape(r.get("date","")) + '</div></div>'
            h += '<div style="text-align:right;"><div style="background:' + c + '; color:#fff; padding:2px 10px; border-radius:12px; font-size:10px; font-weight:700; margin-bottom:5px;">' + escape(kw) + '</div>'
            h += '<a href="' + l + '" target="_blank" style="color:#DC3545; font-size:10px; text-decoration:none; font-weight:700;">기사 🔗</a></div></div>'
    h += '</div>'
    st.markdown(h, unsafe_allow_html=True)