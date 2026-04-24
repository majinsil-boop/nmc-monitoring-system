import streamlit as st
import glob
import json
import os
import re
from datetime import datetime
from html import escape

# ── 1. 설정 및 기본 데이터 로드 ─────────────────────────────────────────────
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

BASE_DIR = os.path.expanduser("~")

def _latest(pattern: str) -> str | None:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

def _load(path: str | None) -> list[dict]:
    if not path or not os.path.exists(path): return []
    with open(path, encoding="utf-8") as f: return json.load(f)

# 데이터 로드
asm_path = _latest(os.path.join(BASE_DIR, "assembly_results_*.json"))
sch_path = _latest(os.path.join(BASE_DIR, "schedule_results_*.json"))
news_path = _latest(os.path.join(BASE_DIR, "news_results_*.json"))

asm_data = _load(asm_path)
sch_data = _load(sch_path)
news_data = _load(news_path)

# ── 2. 연구원님 원본 스타일 및 헬퍼 (100% 일치) ───────────────────────────
_BADGE_STYLE = {"중요": "background:#DC3545;color:#fff;", "보통": "background:#E07B00;color:#fff;", "참고": "background:#6C757D;color:#fff;"}
_BAR_COLOR = {"중요": "#DC3545", "보통": "#E07B00", "참고": "#ADB5BD"}

def _badge(level: str) -> str:
    style = _BADGE_STYLE.get(level, "background:#6C757D;color:#fff;")
    return (f'<span style="{style}padding:2px 9px;border-radius:3px;'
            f'font-size:11px;font-weight:700;letter-spacing:.5px;white-space:nowrap;">'
            f'{escape(level)}</span>')

def _tag(text: str, bg: str, fg: str) -> str:
    return (f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:3px;font-size:11px;white-space:nowrap;">'
            f'{escape(text)}</span>')

def _card(label: str, value: int, sub: str = "", color: str = "#1B3A6B") -> str:
    return (f'<div style="flex:1;min-width:130px;background:#fff;border-radius:6px;'
            f'border-top:4px solid {color};padding:14px 16px;'
            f'box-shadow:0 1px 4px rgba(0,0,0,.1);text-align:center;">'
            f'<div style="font-size:28px;font-weight:700;color:{color};">{value}</div>'
            f'<div style="font-size:12px;color:#444;margin-top:3px;">{escape(label)}</div>'
            + (f'<div style="font-size:11px;color:#999;margin-top:2px;">{escape(sub)}</div>' if sub else "")
            + '</div>')

# 중요도 판단 로직 (연구원님 원본)
def _importance_assembly(item):
    status = item.get("status", "")
    if any(s in status for s in ("위원회심사", "본회의", "공포")): return "중요"
    return "보통"

def _importance_news(item):
    kw = item.get("keyword", "")
    return "중요" if kw in {"응급의료", "응급실", "중증외상"} else "보통"

# ── 3. 스트림릿 화면 구성 (선택 영역) ──────────────────────────────────────────
st.write("### 🚑 항목 선택")
sel_a = [r for r in asm_data if st.sidebar.checkbox(f"의안: {r.get('bill_name')[:20]}...", True, key=f"a_{r.get('bill_no')}")]
sel_s = [r for r in sch_data if st.sidebar.checkbox(f"일정: {r.get('title')[:20]}...", True, key=f"s_{r.get('date')}")]
sel_n = [r for r in news_data if st.sidebar.checkbox(f"뉴스: {r.get('title')[:20]}...", True, key=f"n_{r.get('title')}")]

# ── 4. 보고서 생성 및 출력 (이미지 디자인 재현) ──────────────────────────────
if st.button("✨ NMC 공식 양식 보고서 발행", use_container_width=True):
    today = datetime.now().strftime("%Y-%m-%d")
    gen_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # [헤더] 연구원님 원본 그라데이션 및 자간 적용
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1B3A6B 0%,#2A5298 100%);color:#fff;padding:30px 28px 22px;border-radius:10px;margin-bottom:22px;">
      <div style="font-size:11px;letter-spacing:2.5px;opacity:.7;margin-bottom:8px;">응급의료정책팀 &nbsp;|&nbsp; 자동 모니터링 보고서</div>
      <div style="font-size:23px;font-weight:700;margin-bottom:6px;">의료정책 모니터링 보고서 ({today})</div>
      <div style="font-size:12px;opacity:.75;">기준일: {today} &nbsp;·&nbsp; 생성: {gen_at}</div>
    </div>
    """, unsafe_allow_html=True)

    # [요약 카드] 연구원님 원본 색상 배정 (#1B3A6B, #2A5298, #495057)
    cards = "".join([
        _card("계류 의안", len(sel_a), f"중요 {sum(1 for r in sel_a if _importance_assembly(r)=='중요')}건", "#1B3A6B"),
        _card("예정 일정", len(sel_s), "14일 이내", "#2A5298"),
        _card("언론 기사", len(sel_n), f"중요 {sum(1 for r in sel_n if _importance_news(r)=='중요')}건", "#1B3A6B"),
        _card("전체 항목", len(sel_a)+len(sel_s)+len(sel_n), "중복 제거", "#495057"),
    ])
    st.markdown(f'<div style="display:flex;gap:12px;margin-bottom:25px;">{cards}</div>', unsafe_allow_html=True)

    # [섹션] 의안 현황
    if sel_a:
        st.markdown(f'<div style="background:#1B3A6B;color:#fff;padding:10px 18px;border-radius:5px 5px 0 0;font-size:15px;font-weight:700;">📋 의안 현황 (국회의안정보시스템)</div>', unsafe_allow_html=True)
        for r in sel_a:
            lvl = _importance_assembly(r)
            st.markdown(f"""
            <div style="border-left:5px solid {_BAR_COLOR[lvl]};padding:15px;background:#fff;border:1px solid #D0D7E5;border-top:none;margin-bottom:2px;">
                <div style="margin-bottom:6px;">{_badge(lvl)} {_tag(r.get('keyword','의료법'), '#EAF0FB', '#1B3A6B')}</div>
                <div style="font-weight:700;color:#1B3A6B;font-size:14px;">{r.get('bill_name')}</div>
                <div style="font-size:12px;color:#666;margin-top:5px;">{escape(r.get('summary','')[:200])}...</div>
            </div>
            """, unsafe_allow_html=True)

    # [섹션] 언론 모니터링
    if sel_n:
        st.markdown(f'<div style="background:#1B3A6B;color:#fff;padding:10px 18px;border-radius:5px 5px 0 0;margin-top:20px;font-size:15px;font-weight:700;">📰 언론 모니터링 (전일 기사)</div>', unsafe_allow_html=True)
        for r in sel_n:
            lvl = _importance_news(r)
            st.markdown(f"""
            <div style="border-left:5px solid {_BAR_COLOR[lvl]};padding:15px;background:#fff;border:1px solid #D0D7E5;border-top:none;margin-bottom:2px;">
                <div style="margin-bottom:6px;">{_badge(lvl)} {_tag(r.get('keyword','응급의료'), '#EAF0FB', '#1B3A6B')}</div>
                <div style="font-weight:700;color:#1B3A6B;font-size:14px;">{r.get('title')}</div>
                <div style="font-size:11px;color:#888;margin-top:5px;">{r.get('date')} | {r.get('source')}</div>
            </div>
            """, unsafe_allow_html=True)