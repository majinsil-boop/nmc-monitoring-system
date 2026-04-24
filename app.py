import streamlit as st
import pandas as pd
import glob
import os
import json
import re
from datetime import datetime
from html import escape

# 1. 페이지 설정 및 데이터 로딩 (연구원님 방식)
st.set_page_config(page_title="NMC 응급의료 모니터링 시스템", layout="wide")

def _latest(pattern):
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

def _load(path):
    if not path or not os.path.exists(path): return []
    with open(path, encoding="utf-8") as f: return json.load(f)

# 데이터 로드
asm_path = _latest('assembly_results_*.json')
sch_path = _latest('schedule_results_*.json')
news_path = _latest('news_results_*.json')

assembly_data = _load(asm_path)
schedule_data = _load(sch_path)
news_data = _load(news_path)

# 2. 연구원님 generate_report.py 로직 100% 이식
_URGENT_NEWS_KW = {"응급의료", "응급실", "닥터헬기", "중증외상", "구급", "응급실 뺑뺑이"}
_NORMAL_NEWS_KW = {"필수의료", "공공보건의료법", "구조", "외상"}

def _is_notice_active(notice: str) -> bool:
    if not notice: return False
    m = re.search(r"~\s*(\d{4}-\d{2}-\d{2})", notice)
    if not m: return True
    try:
        end_date = datetime.strptime(m.group(1), "%Y-%m-%d")
        return end_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    except: return True

def _importance_assembly(item: dict) -> str:
    if item.get("legislative_notice") and _is_notice_active(item["legislative_notice"]): return "중요"
    status = item.get("status", "")
    if any(s in status for s in ("위원회심사", "본회의", "공포")): return "중요"
    return "보통"

def _importance_schedule(item: dict) -> str:
    if item.get("is_upcoming"): return "중요" if item.get("topic_keyword") else "보통"
    return "참고"

def _importance_news(item: dict) -> str:
    kw = item.get("keyword", "")
    if kw in _URGENT_NEWS_KW: return "중요"
    if kw in _NORMAL_NEWS_KW: return "보통"
    return "참고"

# 3. 연구원님 코드의 스타일 정의 (임의 이모티콘 모두 삭제)
_BADGE_STYLE = {"중요": "background:#DC3545;color:#fff;", "보통": "background:#E07B00;color:#fff;", "참고": "background:#6C757D;color:#fff;"}
_BAR_COLOR = {"중요": "#DC3545", "보통": "#E07B00", "참고": "#ADB5BD"}

STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    body { background-color: #EEF2F9; }
    .report-wrap { font-family: "Malgun Gothic", sans-serif; background:#EEF2F9; padding:20px; max-width:920px; margin:0 auto; }
    .header { background:linear-gradient(135deg,#1B3A6B 0%,#2A5298 100%) !important; color:#fff !important; padding:35px 30px; border-radius:10px; margin-bottom:20px; -webkit-print-color-adjust: exact; }
    .card-box { display:flex; gap:12px; margin-bottom:20px; }
    .card { flex:1; background:#fff !important; border-radius:6px; padding:15px; text-align:center; box-shadow:0 1px 4px rgba(0,0,0,.1); -webkit-print-color-adjust: exact; }
    .card-val { font-size:26px; font-weight:700; margin-bottom:5px; }
    .sec-header { background:#1B3A6B !important; color:#fff !important; padding:10px 18px; border-radius:5px 5px 0 0; margin-top:25px; display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust: exact; }
    .item-box { background:#fff !important; padding:15px; margin-bottom:10px; border-radius:0 4px 4px 0; box-shadow:0 1px 3px rgba(0,0,0,.07); position:relative; -webkit-print-color-adjust: exact; }
    .keyword-tag { display:inline-block; background:#EAF0FB !important; color:#1B3A6B !important; padding:3px 12px; border-radius:20px; font-size:11px; font-weight:700; margin-right:5px; -webkit-print-color-adjust: exact; }
    .badge { padding:2px 9px; border-radius:3px; font-size:11px; font-weight:700; color:#fff !important; margin-right:6px; -webkit-print-color-adjust: exact; }
    @media print {
        @page { size: A4; margin: 10mm; }
        .stButton { display: none !important; }
        .item-box { page-break-inside: avoid; }
    }
</style>
"""

st.markdown(STYLE, unsafe_allow_html=True)
st.title("🚑 NMC 정책 모니터링 시스템")

# 4. 항목 선택 UI
selected = {'a': [], 's': [], 'n': []}
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("📋 의안 선택")
    for i, r in enumerate(assembly_data):
        if st.checkbox(f"{r.get('bill_name')}", key=f"a{i}"): selected['a'].append(r)
with c2:
    st.subheader("📅 일정 선택")
    for i, r in enumerate(schedule_data):
        if st.checkbox(f"{r.get('title')}", key=f"s{i}"): selected['s'].append(r)
with c3:
    st.subheader("📰 뉴스 선택")
    for i, r in enumerate(news_data):
        if st.checkbox(f"{r.get('title')}", key=f"n{i}"): selected['n'].append(r)

# 5. 보고서 발행 로직
if st.button("✨ NMC 최종 보고서 발행", use_container_width=True):
    total = len(selected['a']) + len(selected['s']) + len(selected['n'])
    today = datetime.now().strftime('%Y-%m-%d')
    
    html = f"""
    <div class="report-wrap">
        <div class="header">
            <div style="font-size:11px; letter-spacing:2.5px; opacity:.7; margin-bottom:8px;">응급의료정책팀 | 자동 모니터링 보고서</div>
            <div style="font-size:26px; font-weight:700;">의료정책 모니터링 보고서 ({today})</div>
        </div>

        <div class="card-box">
            <div class="card" style="border-top:4px solid #DC3545 !important;"><div class="card-val" style="color:#DC3545 !important;">{len(selected['a'])}</div><div style="font-size:12px;">계류 의안</div></div>
            <div class="card" style="border-top:4px solid #E07B00 !important;"><div class="card-val" style="color:#E07B00 !important;">{len(selected['s'])}</div><div style="font-size:12px;">예정 일정</div></div>
            <div class="card" style="border-top:4px solid #1B3A6B !important;"><div class="card-val" style="color:#1B3A6B !important;">{len(selected['n'])}</div><div style="font-size:12px;">언론 기사</div></div>
            <div class="card" style="background:#E9ECEF !important; border-top:4px solid #495057 !important;"><div class="card-val" style="color:#495057 !important;">{total}</div><div style="font-size:12px;">전체</div></div>
        </div>
    """

    configs = [('a', '의안 현황', '📋', _importance_assembly), ('s', '주요 일정', '📅', _importance_schedule), ('n', '언론 모니터링', '📰', _importance_news)]
    for key, title, icon, imp_func in configs:
        if selected[key]:
            html += f'<div class="sec-header"><span>{icon} {title}</span><span>총 {len(selected[key])}건</span></div>'
            for item in selected[key]:
                lvl = imp_func(item)
                color = _BAR_COLOR.get(lvl, "#ADB5BD")
                badge_style = _BADGE_STYLE.get(lvl, "")
                kw = item.get('keyword') or item.get('category') or item.get('topic_keyword') or '응급의료'
                
                html += f"""
                <div class="item-box" style="border-left:5px solid {color} !important;">
                    <div style="margin-bottom:8px;">
                        <span class="badge" style="{badge_style}">{lvl}</span>
                        <span class="keyword-tag">{kw}</span>
                    </div>
                    <div style="font-size:15px; font-weight:700; color:#1B3A6B; margin-bottom:5px;">{item.get('bill_name') or item.get('title')}</div>
                    <div style="font-size:12px; color:#777;">{item.get('date') or item.get('proposed_date') or ''} | {item.get('source', '')}</div>
                    {f'<div style="font-size:13px; color:#333; background:#F8F9FA; padding:10px; border-radius:4px; margin-top:10px; line-height:1.6;">{item.get("summary")}</div>' if item.get("summary") else ""}
                </div>
                """
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)