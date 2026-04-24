import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 설정 및 데이터 로드
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _load_data(pattern):
    curr = os.path.dirname(os.path.abspath(__file__))
    f_path = os.path.join(curr, pattern)
    files = sorted(glob.glob(f_path))
    if not files: return []
    try:
        with open(files[-1], encoding="utf-8") as f:
            return json.load(f)
    except: return []

# [중요] 외부 링크 강제 연결 보정 함수
def fix_url(url):
    if not url or url == "#": return "#"
    u = str(url).strip()
    # 주소가 http로 시작하지 않으면 강제로 https://를 붙임
    if u.startswith("http"):
        return u
    return f"https://{u}"

asm_raw = _load_data("assembly_results_*.json")
sch_raw = _load_data("schedule_results_*.json")
news_raw = _load_data("news_results_*.json")

if "phase" not in st.session_state:
    st.session_state.phase = "SELECT"

# [A] 선택 화면
if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 보고서 생성기")
    sel_a, sel_s, sel_n = [], [], []

    st.subheader("❶ 의안 현황")
    for i, r in enumerate(asm_raw):
        link = fix_url(r.get("link", r.get("bill_link", "#")))
        st.write(f"**{r.get('bill_name','')}**")
        st.markdown(f"<a href='{link}' target='_blank'>🔗 [원문보기]</a>", 
                    unsafe_allow_html=True)
        if st.checkbox("포함", key=f"ca_{i}"):
            sel_a.append(r)
        st.caption(f"📝 요약: {r.get('summary', '요약 없음')}")
        st.write("---")

    st.subheader("❷ 주요 일정")
    for i, r in enumerate(sch_raw):
        link = fix_url(r.get("link", "#"))
        st.write(f"📅 [{r.get('date','')}] **{r.get('title','')}**")
        st.markdown(f"<a href='{link}' target='_blank'>🔗 [원문보기]</a>", 
                    unsafe_allow_html=True)
        if st.checkbox("포함", key=f"cs_{i}"):
            sel_s.append(r)
        st.write("---")

    st.subheader("❸ 언론 모니터링")
    for i, r in enumerate(news_raw):
        link = fix_url(r.get("link", r.get("url", "#")))
        st.write(f"📰 [{r.get('source','')}] **{r.get('title','')}**")
        st.markdown(f"<a href='{link}' target='_blank'>🔗 [기사보기]</a>", 
                    unsafe_allow_html=True)
        if st.checkbox("포함", key=f"cn_{i}"):
            sel_n.append(r)
        st.write("---")

    if st.button("✨ 보고서 발행", use_container_width=True):
        st.session_state.sel_a = sel_a
        st.session_state.sel_s = sel_s
        st.session_state.sel_n = sel_n
        st.session_state.phase = "REPORT"
        st.rerun()

# [B] 보고서 화면 (링크 및 디자인 보강)
else:
    today = datetime.now().strftime("%Y-%m-%d")
    st.sidebar.button("🔙 다시 선택", 
                      on_click=lambda: st.session_state.update({"phase": "SELECT"}))
    
    st.markdown("<style>[data-testid='stHeader'] { display: none; } @media print { header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; } .main { padding: 0 !important; } }</style>", unsafe_allow_html=True)

    html = '<div style="background:#FBFBFB; padding:20px; font-family:sans-serif;">'
    
    # 1. 헤더
    html += '<div style="background:#1B3A6B; color:#fff; padding:20px 30px; '
    html += 'display:flex; justify-content:space-between; align-items:flex-end; '
    html += '-webkit-print-color-adjust:exact; border-radius:10px;">'
    html += '<div><div style="font-size:10px; opacity:0.8;">응급의료정책연구팀</div>'
    html += '<div style="font-size:22px; font-weight:800;">'
    html += '응급의료 동향 모니터링</div></div>'
    html += f'<div style="text-align:right;"><div style="font-size:18px; font-weight:800;">{today}</div></div></div>'

    # 2. 요약 카드
    html += '<div style="display:flex; gap:10px; padding:15px 0;">'
    c_list = [
        ("📋", "의안", len(st.session_state.sel_a), "#EBF1F9"),
        ("📅", "일정", len(st.session_state.sel_s), "#E8F5E9"),
        ("📰", "뉴스", len(st.session_state.sel_n), "#FDECEA"),
        ("📊", "전체", len(st.session_state.sel_a)+len(st.session_state.sel_s)+len(st.session_state.sel_n), "#F3F4F6")
    ]
    for ic, lb, vl, bg in c_list:
        html += f'<div style="flex:1; background:{bg}; border-radius:10px; '
        html += 'padding:12px; display:flex; flex-direction:column; '
        html += 'align-items:center; justify-content:center; gap:5px; -webkit-print-color-adjust:exact;">'
        html += f'<div style="font-size:20px;">{ic}</div>'
        html += f'<div style="font-size:11px; font-weight:700;">{lb}</div>'
        html += f'<div style="font-size:24px; font-weight:800;">{vl}</div></div>'
    html += '</div>'

    # 3. ❶ 의안 (파랑 선)
    if st.session_state.sel_a:
        html += '<div style="margin:10px 0; font-size:16px; font-weight:800; color:#1B3A6B;">❶ 의안 현황</div>'
        for r in st.session_state.sel_a:
            link = fix_url(r.get("link", r.get("bill_link", "#")))
            html += '<div style="background:#fff; border:1px solid #E2E8F0; '
            html += 'border-left:6px solid #1B3A6B; padding:15px; border-radius:12px; '
            html += 'margin-bottom:10px; -webkit-print-color-adjust:exact;">'
            html += '<div style="display:flex; justify-content:space-between; align-items:center;">'
            html += f'<div style="font-size:14px; font-weight:800; color:#1B3A6B;">{escape(r.get("bill_name",""))}</div>'
            html += f'<a href="{link}" target="_blank" style="background:#1B3A6B; color:#fff; '
            html += 'padding:3px 10px; border-radius:5px; font-size:10px; text-decoration:none; '
            html += '-webkit-print-color-adjust:exact;">원문보기 🔗</a></div>'
            html += '<div style="background:#FFF9E6; color:#856404; padding:3px 10px; '
            html += 'border-radius:5px; font-size:11px; font-weight:700; margin:8px 0; '
            html += 'display:inline-block; -webkit-print-color-adjust:exact;">입법예고 진행중</div>'
            html += f'<div style="font-size:11px; color:#444; line-height:1.5;">{escape(r.get("summary",""))}</div></div>'

    # 4. ❷ 주요 일정 (초록 선)
    if st.session_state.sel_s:
        html += '<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">❷ 주요 일정</div>'
        for r in st.session_state.sel_s:
            link = fix_url(r.get("link", "#"))
            html += '<div style="background:#fff; border:1px solid #E2E8F0; '
            html += 'border-left:6px solid #28A745; padding:12px 15px; margin-bottom:8px; '
            html += 'display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust:exact;">'
            html += f'<div><div style="font-size:13px; font-weight:800; color:#333;">{escape(r.get("title",""))}</div>'
            html += '<div style="margin-top:3px;"><span style="background:#E8F5E9; color:#1B5E20; '
            html += 'padding:1px 6px; border-radius:4px; font-size:10px; -webkit-print-color-adjust:exact;">토론회</span></div></div>'
            html += f'<div style="text-align:right;"><div style="font-size:12px; font-weight:800; margin-bottom:5px;">{escape(r.get("date",""))}</div>'
            html += f'<a href="{link}" target="_blank" style="background:#28A745; color:#fff; '
            html += 'padding:2px 8px; border-radius:4px; font-size:10px; text-decoration:none; '
            html += '-webkit-print-color-adjust:exact;">상세보기 🔗</a></div></div>'

    # 5. ❸ 뉴스 (빨강 선)
    if st.session_state.sel_n:
        html += '<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">❸ 언론 모니터링</div>'
        for r in st.session_state.sel_n:
            link = fix_url(r.get("link", r.get("url", "#")))
            kw = r.get("keyword", "응급의료")
            c_h = {"중증응급":"#800000", "중증외상":"#6F42C1"}.get(kw, "#DC3545")
            html += '<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #DC3545; '
            html += 'padding:12px 15px; margin-bottom:10px; display:flex; justify-content:space-between; '
            html += 'align-items:center; -webkit-print-color-adjust:exact;">'
            html += f'<div><div style="font-size:13px; font-weight:800; color:#1B3A6B;">{escape(r.get("title",""))}</div>'
            html += f'<div style="font-size:10px; color:#777; margin-top:3px;">{escape(r.get("source",""))} | {escape(r.get("date",""))}</div></div>'
            html += f'<div style="text-align:right;"><div style="background:{c_h}; color:#fff; padding:2px 10px; '
            html += 'border-radius:12px; font-size:10px; font-weight:700; margin-bottom:5px; -webkit-print-color-adjust:exact;">'
            html += f'{escape(kw)}</div><a href="{link}" target="_blank" style="color:#DC3545; '
            html += 'font-size:10px; text-decoration:none; font-weight:700;">기사보기 🔗</a></div></div>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)