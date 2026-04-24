import streamlit as st
import pandas as pd
import glob
import os
import json
import re
from datetime import datetime, timedelta
from html import escape

# 1. 페이지 설정 및 데이터 로드
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

# 2. 연구원님의 원본 로직 (중요도 판단 등) 100% 그대로 복사
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

# 3. 연구원님의 원본 디자인 헬퍼 (CSS 및 HTML 함수)
_BADGE_STYLE = {"중요": "background:#DC3545;color:#fff;", "보통": "background:#E07B00;color:#fff;", "참고": "background:#6C757D;color:#fff;"}
_BAR_COLOR = {"중요": "#DC3545", "보통": "#E07B00", "참고": "#ADB5BD"}

def _badge_html(level: str) -> str:
    style = _BADGE_STYLE.get(level, "background:#6C757D;color:#fff;")
    return f'<span style="{style}padding:2px 9px;border-radius:3px;font-size:11px;font-weight:700;margin-right:6px;">{escape(level)}</span>'

def _tag_html(text: str, bg: str = "#EAF0FB", fg: str = "#1B3A6B") -> str:
    # 둥근 태그 스타일 (알약 모양)
    return f'<span style="background:{bg};color:{fg};padding:3px 12px;border-radius:20px;font-size:11px;font-weight:700;margin-right:5px;display:inline-block;">{escape(text)}</span>'

def _item_box_style(level: str) -> str:
    color = _BAR_COLOR.get(level, "#ADB5BD")
    return f'border-left:5px solid {color};padding:15px;margin-bottom:10px;background:#fff;border-radius:0 4px 4px 0;box-shadow:0 1px 3px rgba(0,0,0,.07);position:relative;-webkit-print-color-adjust:exact;'

# 4. UI 레이아웃
st.title("🚑 NMC 정책 모니터링 시스템 (통합판)")

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

if st.button("✨ NMC 공식 보고서 발행", use_container_width=True):
    today = datetime.now().strftime("%Y-%m-%d")
    html = f"""
    <div style="background:#EEF2F9; padding:20px; font-family:'Malgun Gothic';">
        <div style="background:linear-gradient(135deg,#1B3A6B 0%,#2A5298 100%); color:#fff; padding:35px 30px; border-radius:10px; margin-bottom:20px; -webkit-print-color-adjust:exact;">
            <div style="font-size:11px; letter-spacing:2.5px; opacity:.7; margin-bottom:8px;">응급의료정책팀 | 자동 모니터링 보고서</div>
            <div style="font-size:26px; font-weight:700;">의료정책 모니터링 보고서 ({today})</div>
        </div>

        <div style="display:flex; gap:12px; margin-bottom:10px;">
            <div style="flex:1; background:#fff; border-radius:6px; border-top:4px solid #DC3545; padding:15px; text-align:center; box-shadow:0 1px 4px rgba(0,0,0,.1); -webkit-print-color-adjust:exact;">
                <div style="font-size:28px; font-weight:700; color:#DC3545;">{len(selected['a'])}</div><div style="font-size:12px;">계류 의안</div>
            </div>
            <div style="flex:1; background:#fff; border-radius:6px; border-top:4px solid #FFB703; padding:15px; text-align:center; box-shadow:0 1px 4px rgba(0,0,0,.1); -webkit-print-color-adjust:exact;">
                <div style="font-size:28px; font-weight:700; color:#FFB703;">{len(selected['s'])}</div><div style="font-size:12px;">📍 예정 일정</div>
            </div>
            <div style="flex:1; background:#fff; border-radius:6px; border-top:4px solid #1B3A6B; padding:15px; text-align:center; box-shadow:0 1px 4px rgba(0,0,0,.1); -webkit-print-color-adjust:exact;">
                <div style="font-size:28px; font-weight:700; color:#1B3A6B;">{len(selected['n'])}</div><div style="font-size:12px;">언론 기사</div>
            </div>
            <div style="flex:1; background:#E9ECEF; border-radius:6px; border-top:4px solid #495057; padding:15px; text-align:center; box-shadow:0 1px 4px rgba(0,0,0,.1); -webkit-print-color-adjust:exact;">
                <div style="font-size:28px; font-weight:700; color:#495057;">{len(selected['a'])+len(selected['s'])+len(selected['n'])}</div><div style="font-size:12px;">전체</div>
            </div>
        </div>
    """

    # 섹션별 데이터 렌더링
    configs = [('a', '의안 현황', '📋', _importance_assembly), ('s', '주요 일정', '📅', _importance_schedule), ('n', '언론 모니터링', '📰', _importance_news)]
    for key, title, icon, imp_func in configs:
        if selected[key]:
            html += f'<div style="background:#1B3A6B; color:#fff; padding:10px 18px; border-radius:5px 5px 0 0; margin-top:25px; display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust:exact;">'
            html += f'<span style="font-size:15px; font-weight:700;">{icon}&nbsp;{title}</span><span style="font-size:12px;">총 {len(selected[key])}건</span></div>'
            html += '<div style="border:1px solid #D0D7E5; border-top:none; border-radius:0 0 5px 5px; padding:15px; background:#fff;">'
            
            for item in selected[key]:
                lvl = imp_func(item)
                html += f'<div style="{_item_box_style(lvl)}">'
                html += f'<div style="margin-bottom:8px;">{_badge_html(lvl)}'
                
                # 태그 로직
                kw = item.get('keyword') or item.get('topic_keyword') or item.get('category') or "응급의료"
                html += _tag_html(kw)
                if key == 's': html += _tag_html("📍 예정", "#D4EDDA", "#155724")
                html += '</div>'
                
                # 제목 및 본문
                title_txt = item.get('bill_name') or item.get('title')
                html += f'<div style="font-size:14px; font-weight:700; color:#1B3A6B; margin-bottom:5px;">{title_txt}</div>'
                
                if key == 'a':
                    html += f'<div style="font-size:12px; color:#555; background:#F8F9FA; padding:8px; border-radius:3px; margin:8px 0;">{item.get("summary", "")}</div>'
                    html += f'<div style="font-size:11px; color:#888;">발의: {item.get("proposed_date")} | 상태: {item.get("status")}</div>'
                elif key == 's':
                    html += f'<div style="font-size:12px; color:#444;">📍 <b>일시 및 장소:</b> {item.get("date")} | {item.get("source")}</div>'
                else:
                    html += f'<div style="font-size:11px; color:#888;">{item.get("source")} | {item.get("date")}</div>'
                
                html += '</div>'
            html += '</div>'

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    st.download_button("💾 보고서 파일(.html) 다운로드", data=html, file_name=f"NMC_Report_{datetime.now().strftime('%m%d')}.html", mime="text/html")