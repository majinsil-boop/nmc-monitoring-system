import streamlit as st
import pandas as pd
import glob
import os
import json
import re
from datetime import datetime, timedelta
from html import escape

# 1. 연구원님 generate_report.py의 로직과 설정을 그대로 변수에 담았습니다.
BASE_DIR = os.getcwd()
_URGENT_NEWS_KW = {"응급의료", "응급실", "닥터헬기", "중증외상", "구급", "응급실 뺑뺑이"}
_NORMAL_NEWS_KW = {"필수의료", "공공보건의료법", "구조", "외상"}

# 중요도 판단 로직 (원본 보존)
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

# 원본 스타일 및 배지 헬퍼 (원본 보존)
_BADGE_STYLE = {"중요": "background:#DC3545;color:#fff;", "보통": "background:#E07B00;color:#fff;", "참고": "background:#6C757D;color:#fff;"}
_BAR_COLOR = {"중요": "#DC3545", "보통": "#E07B00", "참고": "#ADB5BD"}

def _badge(level: str) -> str:
    style = _BADGE_STYLE.get(level, "background:#6C757D;color:#fff;")
    return f'<span style="{style}padding:2px 9px;border-radius:3px;font-size:11px;font-weight:700;letter-spacing:.5px;white-space:nowrap;">{escape(level)}</span>'

def _tag(text: str, bg: str, fg: str) -> str:
    return f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:3px;font-size:11px;white-space:nowrap;">{escape(text)}</span>'

def _bar_style(level: str) -> str:
    color = _BAR_COLOR.get(level, "#ADB5BD")
    return f'border-left:5px solid {color};padding:11px 14px;margin-bottom:8px;background:#fff;border-radius:0 4px 4px 0;box-shadow:0 1px 3px rgba(0,0,0,.07);'

def _card(label: str, value: int, sub: str = "", color: str = "#1B3A6B") -> str:
    return f'<div style="flex:1;min-width:130px;background:#fff;border-radius:6px;border-top:4px solid {color};padding:14px 16px;box-shadow:0 1px 4px rgba(0,0,0,.1);text-align:center;"><div style="font-size:28px;font-weight:700;color:{color};">{value}</div><div style="font-size:12px;color:#444;margin-top:3px;">{escape(label)}</div><div style="font-size:11px;color:#999;margin-top:2px;">{escape(sub)}</div></div>'

# 3. Streamlit 앱 인터페이스
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _latest(pattern):
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

def _load(path):
    if not path or not os.path.exists(path): return []
    with open(path, encoding="utf-8") as f: return json.load(f)

# 데이터 로드
asm_data = _load(_latest('assembly_results_*.json'))
sch_data = _load(_latest('schedule_results_*.json'))
news_data = _load(_latest('news_results_*.json'))

st.title("🚑 NMC 정책 모니터링 시스템")

selected = {'a': [], 's': [], 'n': []}
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("📋 의안 선택")
    for i, r in enumerate(asm_data):
        if st.checkbox(f"{r.get('bill_name')}", key=f"a{i}"): selected['a'].append(r)
with c2:
    st.subheader("📅 일정 선택")
    for i, r in enumerate(sch_data):
        if st.checkbox(f"{r.get('title')}", key=f"s{i}"): selected['s'].append(r)
with c3:
    st.subheader("📰 뉴스 선택")
    for i, r in enumerate(news_data):
        if st.checkbox(f"{r.get('title')}", key=f"n{i}"): selected['n'].append(r)

# 4. 보고서 생성 및 HTML 저장 (전부 포함)
if st.button("✨ NMC 공식 보고서 발행", use_container_width=True):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    gen_at = now.strftime("%Y-%m-%d %H:%M")
    
    # 상단 요약 카드 (원본 색상 로직 적용)
    cards = "".join([
        _card("계류 의안", len(selected['a']), f"선택 {len(selected['a'])}건", "#1B3A6B"),
        _card("예정 일정", len(selected['s']), "14일 이내", "#2A5298"),
        _card("언론 기사", len(selected['n']), f"선택 {len(selected['n'])}건", "#1B3A6B"),
        _card("전체 항목", len(selected['a'])+len(selected['s'])+len(selected['n']), "중복 제거", "#495057"),
    ])

    html = f"""
    <div style="background:#EEF2F9; padding:20px; font-family:'Malgun Gothic';">
        <div style="background:linear-gradient(135deg,#1B3A6B 0%,#2A5298 100%); color:#fff; padding:30px 28px 22px; border-radius:0 0 10px 10px; margin-bottom:22px;">
            <div style="font-size:11px;opacity:.7;margin-bottom:8px;">응급의료정책팀 | 자동 모니터링 보고서</div>
            <div style="font-size:23px;font-weight:700;">의료정책 모니터링 보고서 ({today})</div>
            <div style="font-size:12px;opacity:.75;">생성: {gen_at}</div>
        </div>
        <div style="display:flex;gap:12px;margin-bottom:8px;">{cards}</div>
    """

    # 섹션별 렌더링 (연구원님의 헬퍼 함수들 사용)
    for key, title, icon, imp_func in [('a', '의안 현황', '📋', _importance_assembly), 
                                      ('s', '일정 현황', '📅', _importance_schedule), 
                                      ('n', '언론 모니터링', '📰', _importance_news)]:
        if selected[key]:
            html += f'<div style="background:#1B3A6B;color:#fff;padding:10px 18px;border-radius:5px 5px 0 0;margin-top:28px;display:flex;justify-content:space-between;align-items:center;">'
            html += f'<span style="font-size:15px;font-weight:700;">{icon}&nbsp;{title}</span><span style="font-size:12px;">총 {len(selected[key])}건</span></div>'
            html += '<div style="border:1px solid #D0D7E5;border-top:none;border-radius:0 0 5px 5px;padding:15px;background:#fff;">'
            for item in selected[key]:
                lvl = imp_func(item)
                html += f'<div style="{_bar_style(lvl)}">{_badge(lvl)}{_tag(item.get("keyword", "응급의료"), "#EAF0FB", "#1B3A6B")}'
                html += f'<div style="font-size:14px;font-weight:700;color:#1B3A6B;margin:5px 0;">{item.get("bill_name") or item.get("title")}</div>'
                if item.get("summary"): html += f'<div style="font-size:12px;color:#555;background:#F8F9FA;padding:8px;border-radius:3px;margin:8px 0;">{item.get("summary")}</div>'
                html += f'<div style="font-size:11px;color:#888;">{item.get("proposed_date") or item.get("date") or ""} | {item.get("source", "")}</div></div>'
            html += '</div>'

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    
    # 5. 파일 저장 기능 (원본 요청 사항)
    file_name = f"보고서_{now.strftime('%Y%m%d')}.html"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(html)
    st.success(f"✅ {file_name} 파일이 저장되었습니다.")
    st.download_button("💾 보고서 파일 다운로드", data=html, file_name=file_name, mime="text/html")