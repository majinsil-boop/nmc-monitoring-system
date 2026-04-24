import streamlit as st
import pandas as pd
import glob
import os
import re
import json
from datetime import datetime, timedelta

# --- 1. 연구원님의 로직 그대로 반영 (중요도 판단 등) ---
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
    return "중요" if item.get("topic_keyword") else "보통"

def _importance_news(item: dict) -> str:
    kw = item.get("keyword", "")
    if kw in _URGENT_NEWS_KW: return "중요"
    if kw in _NORMAL_NEWS_KW: return "보통"
    return "참고"

# --- 2. 연구원님의 HTML 디자인 그대로 반영 (CSS 스타일) ---
STYLE = """
<style>
    .report-wrap { font-family: "Malgun Gothic", sans-serif; background:#EEF2F9; padding:20px; color:#222; }
    .header { background:linear-gradient(135deg,#1B3A6B 0%,#2A5298 100%); color:#fff; padding:30px; border-radius:10px; margin-bottom:22px; }
    .card-box { display:flex; gap:12px; margin-bottom:20px; overflow-x:auto; }
    .card { flex:1; min-width:140px; background:#fff; border-radius:6px; border-top:4px solid #1B3A6B; padding:15px; box-shadow:0 1px 4px rgba(0,0,0,.1); text-align:center; }
    .card-val { font-size:24px; font-weight:700; color:#1B3A6B; }
    .sec-header { background:#1B3A6B; color:#fff; padding:10px 18px; border-radius:5px 5px 0 0; margin-top:25px; display:flex; justify-content:space-between; align-items:center; }
    .item-box { background:#fff; border-left:5px solid #ADB5BD; padding:12px; margin-bottom:8px; border-radius:0 4px 4px 0; box-shadow:0 1px 3px rgba(0,0,0,.07); }
    .badge { padding:2px 8px; border-radius:3px; font-size:11px; font-weight:700; color:#fff; margin-right:5px; }
    .badge-중요 { background:#DC3545; }
    .badge-보통 { background:#E07B00; }
    .badge-참고 { background:#6C757D; }
    .item-title { font-size:14px; font-weight:600; color:#1B3A6B; text-decoration:none; display:block; margin:5px 0; }
    .summary-text { font-size:12px; color:#555; background:#F8F9FA; padding:8px; border-radius:3px; margin-top:5px; line-height:1.5; }
</style>
"""

# --- 3. Streamlit 앱 로직 ---
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _latest(pattern):
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

df_a = pd.read_json(_latest('assembly_results_*.json')) if _latest('assembly_results_*.json') else pd.DataFrame()
df_s = pd.read_json(_latest('schedule_results_*.json')) if _latest('schedule_results_*.json') else pd.DataFrame()
df_n = pd.read_json(_latest('news_results_*.json')) if _latest('news_results_*.json') else pd.DataFrame()

st.title("🚑 NMC 정책 모니터링 보고서 생성기")

# 항목 선택
selected = {'a': [], 's': [], 'n': []}
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("📋 의안 선택")
    for i, r in df_a.iterrows():
        if st.checkbox(f"{r.get('bill_name')}", key=f"a{i}"): selected['a'].append(r.to_dict())
with c2:
    st.subheader("📅 일정 선택")
    for i, r in df_s.iterrows():
        if st.checkbox(f"{r.get('title')}", key=f"s{i}"): selected['s'].append(r.to_dict())
with c3:
    st.subheader("📰 뉴스 선택")
    for i, r in df_n.iterrows():
        if st.checkbox(f"{r.get('title')}", key=f"n{i}"): selected['n'].append(r.to_dict())

if st.button("✨ NMC 양식으로 보고서 발행", use_container_width=True):
    total = len(selected['a']) + len(selected['s']) + len(selected['n'])
    
    html = f"{STYLE}<div class='report-wrap'>"
    # 헤더
    html += f"""
    <div class="header">
        <div style="font-size:11px; letter-spacing:2.5px; opacity:.7; margin-bottom:8px;">응급의료정책팀 | 자동 모니터링 보고서</div>
        <div style="font-size:23px; font-weight:700;">의료정책 모니터링 보고서 ({datetime.now().strftime('%Y-%m-%d')})</div>
    </div>
    """
    # 요약 카드
    html += f"""
    <div class="card-box">
        <div class="card"><div class="card-val">{len(selected['a'])}</div><div style="font-size:12px;">계류 의안</div></div>
        <div class="card" style="border-top-color:#FFB703;"><div class="card-val" style="color:#FFB703;">{len(selected['s'])}</div><div style="font-size:12px;">📍 예정 일정</div></div>
        <div class="card"><div class="card-val">{len(selected['n'])}</div><div style="font-size:12px;">언론 기사</div></div>
        <div class="card" style="background:#f1f3f5;"><div class="card-val" style="color:#495057;">{total}</div><div style="font-size:12px;">전체 항목</div></div>
    </div>
    """

    # 섹션 빌더
    for key, title, icon, imp_func in [('a', '의안 현황', '📋', _importance_assembly), 
                                      ('s', '주요 일정', '📅', _importance_schedule), 
                                      ('n', '언론 모니터링', '📰', _importance_news)]:
        if selected[key]:
            html += f'<div class="sec-header"><span>{icon} {title}</span><span>총 {len(selected[key])}건</span></div>'
            for item in selected[key]:
                lvl = imp_func(item)
                color = "#DC3545" if lvl == "중요" else ("#E07B00" if lvl == "보통" else "#ADB5BD")
                html += f"""
                <div class="item-box" style="border-left-color:{color};">
                    <span class="badge badge-{lvl}">{lvl}</span>
                    <a href="{item.get('url', '#')}" class="item-title" target="_blank">{item.get('bill_name') or item.get('title')}</a>
                    <div style="font-size:11px; color:#888;">{item.get('proposed_date') or item.get('date', '')} | {item.get('source', '')}</div>
                    {f'<div class="summary-text">{item.get("summary")[:200]}...</div>' if item.get("summary") else ""}
                </div>
                """
    
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    st.download_button("💾 보고서 다운로드(.html)", data=html, file_name=f"NMC_Report_{datetime.now().strftime('%m%d')}.html", mime="text/html")