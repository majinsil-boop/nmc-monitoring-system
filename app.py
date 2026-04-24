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
    
    sel_a, sel_s, sel_n = [], [], []

    st.subheader("❶ 의안 현황")
    for i, r in enumerate(asm_raw):
        link = r.get('link', r.get('bill_link', '#'))
        st.markdown(f"**{r.get('bill_name','')}**")
        st.markdown(f"<a href='{link}' target='_blank'>🔗 [원문보기]</a>", 
                    unsafe_allow_html=True)
        if st.checkbox("이 의안 포함", key=f"ca_{i}"):
            sel_a.append(r)
        st.caption(f"📝 요약: {r.get('summary', '요약 없음')}")
        st.write("---")

    st.subheader("❷ 주요 일정")
    for i, r in enumerate(sch_raw):
        link = r.get('link', '#')
        st.write(f"📅 [{r.get('date','')}] **{r.get('title','')}**")
        st.markdown(f"<a href='{link}' target='_blank'>🔗 [원문보기]</a>", 
                    unsafe_allow_html=True)
        if st.checkbox("이 일정 포함", key=f"cs_{i}"):
            sel_s.append(r)
        st.write("---")

    st.subheader("❸ 언론 모니터링")
    for i, r in enumerate(news_raw):
        link = r.get('link', r.get('url', '#'))
        st.write(f"📰 [{r.get('source','')}] **{r.get('title','')}**")
        st.markdown(f"<a href='{link}' target='_blank'>🔗 [기사보기]</a>", 
                    unsafe_allow_html=True)
        if st.checkbox("이 뉴스 포함", key=f"cn_{i}"):
            sel_n.append(r)
        st.write("---")

    if st.button("✨ 보고서 발행", use_container_width=True):
        st.session_state.sel_a = sel_a
        st.session_state.sel_s = sel_s
        st.session_state.sel_n = sel_n
        st.session_state.phase = "REPORT"
        st.rerun()

# [B] 보고서 화면 (모든 긴 문장을 여러 줄로 결합)
else:
    today = datetime.now().strftime("%Y-%m-%d")
    st.sidebar.button("🔙 다시 선택하기", 
                      on_click=lambda: st.session_state.update({"phase": "SELECT"}))
    
    st.markdown("<style>[data-testid='stHeader'] { display: none; } @media print { header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; } .main { padding: 0 !important; } .report-container { transform: scale(0.96); transform-origin: top center; } }</style>", unsafe_allow_html=True)

    html = '<div class="report-container" '
    html += 'style="background:#FBFBFB; padding:20px; font-family:sans-serif;">'
    
    # 헤더
    html += '<div style="background:#1B3A6B; color:#fff; padding:20px 30px; '
    html += 'display:flex; justify-content:space-between; '
    html += 'align-items:flex-end; -webkit-print-color-adjust:exact; '
    html += 'border-radius:10px;">'
    html += '<div><div style="font-size:10px; opacity:0.8;">'
    html += '응급의료정책연구팀</div>'
    html += '<div style="font-size:22px; font-weight:800;">'
    html += '응급의료 동향 모니터링</div></div>'
    html += '<div style="text-align:right;"><div style="font-size:18px; '
    html += f'font-weight:800;">{today}</div></div></div>'

    # 요약 카드
    html += '<div style="display:flex; gap:10px; padding:15px 0;">'
    c_list = [
        ("📋", "의안", len(st.session_state.sel_a), "#EBF1F9"),
        ("📅", "일정", len(st.session_state.sel_s), "#E8F5E9"),
        ("📰", "뉴스", len(st.session_state.sel_n), "#FDECEA"),
        ("📊", "전체", len(st.session_state.sel_a)+len(st.session_state.sel_s)+len(st.session_state.sel_n), "#F3F4F6")
    ]
    for icon, label, val, bg in c_list:
        html += f'<div style="flex:1; background:{bg}; border-radius:10px; '
        html += 'padding:12px; display:flex; flex-direction:column; '
        html += 'align-items:center; justify-content:center; gap:5px; '
        html += '-webkit-print-color-adjust:exact;">'
        html += f'<div style="font-size:20px;">{icon}</div>'
        html += f'<div style="font-size:11px; font-weight:700;">{label}</div>'
        html += f'<div style="font-size:24px; font-weight:800;">{val}</div></div>'
    html += '</div>'

    # ❶ 의안 (파랑 선)
    if st.session_state.sel_a:
        html += '<div style="margin:10px 0; font-size:16px; font-weight:800; '
        html += 'color:#1B3A6B;">❶ 의안 현황</div>'
        for r in st.session_state.sel_a:
            link = r.get('link', r.get('bill_link', '#'))
            html += '<div style="background:#fff; border:1px solid #E2E8F0; '
            html += 'border-left:6px solid #1B3A6B; padding:15px; '
            html += 'border-radius:12px; margin-bottom:10px; '
            html += '-webkit-print-color-adjust:exact;">'
            html += '<div style="display:flex; justify-content:space-between; '
            html += 'align-items:center; margin-bottom:8px;">'
            html += f'<a href="{link}" target="_blank" style="text-decoration:none; '
            html += f'font-size:14px; font-weight:800; color:#1B3A6B;">'
            html += f'{escape(r.get("bill_name",""))} 🔗</a>'
            html += '<div style="background:#1B3A6B; color:#fff; '
            html += 'padding:2px 10px; border-radius:12px; font-size:10px; '
            html += '-webkit-print-color-adjust:exact;">접수</div></div>'
            html += '<div style="background:#FFF9E6; border:1px solid #FFD966; '
            html += 'color:#856404; padding:3px 10px; border-radius:5px; '
            html += 'font-size:11px; font-weight:700; margin-bottom:8px; '
            html += 'display:inline-block; -webkit-print-color-adjust:exact;">'
            html += '입법예고 진행중</div>'
            html += f'<div style="font-size:11px; color:#444; line-height:1.5;">'
            html += f'{escape(r.get("summary",""))}</div></div>'

    # ❷ 일정 (초록 선)
    if st.session_state.sel_s:
        html += '<div style="margin:20px 0 10px; font-size:16px; '
        html += 'font-weight:800; color:#1B3A6B;">❷ 주요 일정</div>'
        for r in st.session_state.sel_s:
            link = r.get('link', '#')
            html += '<div style="background:#fff; border:1px solid #E2E8F0; '
            html += 'border-left:6px solid #28A745; padding:12px 15px; '
            html += 'margin-bottom:8px; display:flex; '
            html += 'justify-content:space-between; align-items:center; '
            html += '-webkit-print-color-adjust:exact;">'
            html += f'<div><a href="{link}" target="_blank" style="'
            html += 'text-decoration:none; font-size:13px; font-weight:800; '
            html += f'color:#333;">{escape(r.get("title",""))} 🔗</a>'
            html += '<div style="margin-top:3px;"><span style="'
            html += 'background:#E8F5E9; color:#1B5E20; padding:1px 6px; '
            html += 'border-radius:4px; font-size:10px; font-weight:700; '
            html += '-webkit-print-color-adjust:exact;">토론회</span></div></div>'
            html += f'<div style="font-size:12px; font-weight:800;">'
            html += f'{escape(r.get("date",""))}</div></div>'

    # ❸ 뉴스 (빨간 선)
    if st.session_state.sel_n:
        html += '<div style="margin:20px 0 10px; font-size:16px; '
        html += 'font-weight:800; color:#1B3A6B;">❸ 언론 모니터링</div>'
        for r in st.session_state.sel_n:
            link = r.get('link', r.get('url', '#'))
            kw = r.get('keyword','응급의료')
            c_hex = {"중증응급":"#800000", "중증외상":"#6F42C1", 
                     "상급종합병원":"#A52A2A"}.get(kw, "#DC3545")
            html += '<div style="background:#fff; border:1px solid #E2E8F0; '
            html += f'border-left:6px solid #DC3545; padding:12px 15px; '
            html += 'margin-bottom:10px; display:flex; '
            html += 'justify-content:space-between; align-items:center; '
            html += '-webkit-print-color-adjust:exact;">'
            html += f'<div><a href="{link}" target="_blank" style="'
            html += 'text-decoration:none; font-size:13px; font-weight:800; '
            html += f'color:#1B3A6B;">{escape(r.get("title",""))} 🔗</a>'
            html += f'<div style="font-size:10px; color:#777; margin-top:3px;">'
            html += f'{escape(r.get("source",""))} | '
            html += f'{escape(r.get("date",""))}</div></div>'
            html += f'<div style="background:{c_hex}; color:#fff; '
            html += 'padding:2px 10px; border-radius:12px; font-size:10px; '
            html += f'font-weight:700; -webkit-print-color-adjust:exact;">'
            html += f'{escape(kw)}</div></div>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)