import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 설정 및 데이터 로드
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

# [핵심] 외부 링크 강제 보정 함수
def fix_url(url):
    if not url or url == "#": return "#"
    u = str(url).strip()
    if u.startswith("http"): return u
    # 주소에 마침표(.)가 있으면 외부 도메인이므로 https:// 강제 삽입
    if "." in u: return "https://" + u
    return u

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
    sel_a, sel_s, sel_n = [], [], []

    st.subheader("❶ 의안 현황")
    for i, r in enumerate(asm_raw):
        link = fix_url(r.get('link', r.get('bill_link', '#')))
        col_t, col_l = st.columns([0.8, 0.2])
        with col_t:
            if st.checkbox(f"[{r.get('status','접수')}] {r.get('bill_name','')}", key=f"check_a_{i}"):
                sel_a.append(r)
        with col_l:
            if link != '#': st.markdown(f"[🔗 원문보기]({link})")

    st.write("---")
    st.subheader("❷ 주요 일정")
    for i, r in enumerate(sch_raw):
        link = fix_url(r.get('link', '#'))
        col_t, col_l = st.columns([0.8, 0.2])
        with col_t:
            if st.checkbox(f"📅 [{r.get('date','')}] {r.get('title','')}", key=f"check_s_{i}"):
                sel_s.append(r)
        with col_l:
            if link != '#': st.markdown(f"[🔗 원문보기]({link})")

    st.write("---")
    st.subheader("❸ 언론 모니터링")
    for i, r in enumerate(news_raw):
        link = fix_url(r.get('link', r.get('url', '#')))
        col_t, col_l = st.columns([0.8, 0.2])
        with col_t:
            if st.checkbox(f"📰 [{r.get('source','')}] {r.get('title','')}", key=f"check_n_{i}"):
                sel_n.append(r)
        with col_l:
            if link != '#': st.markdown(f"[🔗 기사보기]({link})")

    if st.button("✨ 보고서 발행", use_container_width=True):
        st.session_state.sel_a, st.session_state.sel_s, st.session_state.sel_n = sel_a, sel_s, sel_n
        st.session_state.phase = "REPORT"
        st.rerun()

# [B] 보고서 화면
else:
    today = datetime.now().strftime("%Y-%m-%d")
    st.sidebar.button("🔙 다시 선택하기", on_click=lambda: st.session_state.update({"phase":"SELECT"}))
    
    if not (st.session_state.sel_a or st.session_state.sel_s or st.session_state.sel_n):
        st.warning("선택된 항목이 없습니다.")
        st.stop()

    st.markdown("<style>[data-testid='stHeader'] { display: none; } @media print { header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; } .main { padding: 0 !important; } }</style>", unsafe_allow_html=True)

    html = '<div style="background:#FBFBFB; padding:20px; font-family:sans-serif;">'
    
    # 헤더
    html += f'<div style="background:#1B3A6B; color:#fff; padding:20px 30px; display:flex; justify-content:space-between; align-items:flex-end; -webkit-print-color-adjust:exact; border-radius:10px;">'
    html += '<div><div style="font-size:10px; opacity:0.8;">응급의료정책연구팀</div><div style="font-size:22px; font-weight:800;">응급의료 동향 모니터링</div></div>'
    html += f'<div style="text-align:right;"><div style="font-size:18px; font-weight:800;">{today}</div></div></div>'

    # 요약 카드
    html += '<div style="display:flex; gap:10px; padding:15px 0;">'
    for ic, lb, vl, bg in [("📋","의안",len(st.session_state.sel_a),"#EBF1F9"), ("📅","일정",len(st.session_state.sel_s),"#E8F5E9"), ("📰","뉴스",len(st.session_state.sel_n),"#FDECEA"), ("📊","전체",len(st.session_state.sel_a)+len(st.session_state.sel_s)+len(st.session_state.sel_n),"#F3F4F6")]:
        html += f'<div style="flex:1; background:{bg}; border-radius:10px; padding:12px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:5px; -webkit-print-color-adjust:exact;"><div style="font-size:18px;">{ic}</div><div style="font-size:11px; font-weight:700;">{lb}</div><div style="font-size:24px; font-weight:800;">{vl}</div></div>'
    html += '</div>'

    # ❶ 의안
    if st.session_state.sel_a:
        html += '<div style="margin:10px 0; font-size:16px; font-weight:800; color:#1B3A6B;">❶ 의안 현황</div>'
        for r in st.session_state.sel_a:
            l = fix_url(r.get('link', r.get('bill_link', '#')))
            html += f'<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #1B3A6B; padding:15px; border-radius:12px; margin-bottom:10px; -webkit-print-color-adjust:exact;">'
            html += f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">'
            html += f'<a href="{l}" target="_blank" style="text-decoration:none; font-size:14px; font-weight:800; color:#1B3A6B;">{escape(r.get("bill_name",""))} 🔗</a>'
            html += f'<div style="background:#1B3A6B; color:#fff; padding:2px 10px; border-radius:12px; font-size:10px;">접수</div></div>'
            html += f'<div style="font-size:11px; color:#444; line-height:1.5;">{escape(r.get("summary",""))}</div></div>'

    # ❷ 일정
    if st.session_state.sel_s:
        html += '<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">❷ 주요 일정</div>'
        for r in st.session_state.sel_s:
            l = fix_url(r.get('link', '#'))
            html += f'<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #28A745; padding:12px 15px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust:exact;">'
            html += f'<div><a href="{l}" target="_blank" style="text-decoration:none; font-size:13px; font-weight:800; color:#333;">{escape(r.get("title",""))} 🔗</a><div style="margin-top:3px;"><span style="background:#E8F5E9; color:#1B5E20; padding:1px 6px; border-radius:4px; font-size:10px; font-weight:700;">일정</span></div></div>'
            html += f'<div style="font-size:12px; font-weight:800;">{escape(r.get("date",""))}</div></div>'

    # ❸ 뉴스
    if st.session_state.sel_n:
        html += '<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">❸ 언론 모니터링</div>'
        for r in st.session_state.sel_n:
            l = fix_url(r.get('link', r.get('url', '#')))
            kw = r.get('keyword','응급의료'); c_h = {"중증응급":"#800000", "중증외상":"#6F42C1"}.get(kw, "#DC3545")
            html += f'<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #DC3545; padding:12px 15px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust:exact;">'
            html += f'<div><a href="{l}" target="_blank" style="text-decoration:none; font-size:13px; font-weight:800; color:#1B3A6B;">{escape(r.get("title",""))} 🔗</a><div style="font-size:10px; color:#777; margin-top:3px;">{escape(r.get("source",""))} | {escape(r.get("date",""))}</div></div>'
            html += f'<div style="background:{c_h}; color:#fff; padding:2px 10px; border-radius:12px; font-size:10px; font-weight:700;">{escape(kw)}</div></div>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)