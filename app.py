import streamlit as st
import pandas as pd
import glob
import os
import json
import re
from datetime import datetime, timedelta
from html import escape

# 1. 연구원님 코드의 스타일 헬퍼 (토씨 하나 안 틀리고 그대로 복사)
_BADGE_STYLE = {"중요": "background:#DC3545;color:#fff;", "보통": "background:#E07B00;color:#fff;", "참고": "background:#6C757D;color:#fff;"}
_BAR_COLOR = {"중요": "#DC3545", "보통": "#E07B00", "참고": "#ADB5BD"}

# [핵심] 연구원님 원본의 사각형 태그 스타일 (border-radius: 3px)
def _tag(text: str, bg: str, fg: str) -> str:
    return (f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:3px;font-size:11px;white-space:nowrap;">'
            f'{escape(text)}</span>')

# [핵심] 연구원님 원본의 요약 카드 스타일 (border-top: 4px)
def _card(label: str, value: int, sub: str = "", color: str = "#1B3A6B") -> str:
    return (
        f'<div style="flex:1;min-width:130px;background:#fff;border-radius:6px;'
        f'border-top:4px solid {color};padding:14px 16px;'
        f'box-shadow:0 1px 4px rgba(0,0,0,.1);text-align:center;">'
        f'<div style="font-size:28px;font-weight:700;color:{color};">{value}</div>'
        f'<div style="font-size:12px;color:#444;margin-top:3px;">{escape(label)}</div>'
        + (f'<div style="font-size:11px;color:#999;margin-top:2px;">{escape(sub)}</div>' if sub else "")
        + '</div>'
    )

def _bar_style(level: str) -> str:
    color = _BAR_COLOR.get(level, "#ADB5BD")
    return (f'border-left:5px solid {color};padding:11px 14px;margin-bottom:8px;'
            f'background:#fff;border-radius:0 4px 4px 0;'
            f'box-shadow:0 1px 3px rgba(0,0,0,.07);')

# ... (중요도 판단 로직 생략: 연구원님 원본과 동일)

# 2. 보고서 발행 버튼 클릭 시 실행되는 HTML 조립부
if st.button("✨ NMC 공식 양식 보고서 발행", use_container_width=True):
    today = datetime.now().strftime("%Y-%m-%d")
    
    # [수정완료] 연구원님 원본의 요약 카드 색상 배정 100% 일치
    cards_html = "".join([
        _card("계류 의안", len(selected['a']), f"중요 {sum(1 for r in selected['a'] if _importance_assembly(r)=='중요')}건", "#1B3A6B"),
        _card("예정 일정", len(selected['s']), "14일 이내", "#2A5298"),
        _card("언론 기사", len(selected['n']), f"중요 {sum(1 for r in selected['n'] if _importance_news(r)=='중요')}건", "#1B3A6B"),
        _card("전체 항목", len(selected['a'])+len(selected['s'])+len(selected['n']), "중복 제거", "#495057"),
    ])

    # [수정완료] 언론 모니터링 섹션의 키워드 배지 디자인 100% 일치
    if selected['n']:
        # ... 섹션 헤더 생략 ...
        for item in selected['n']:
            lvl = _importance_news(item)
            html += f'<div style="{_bar_style(lvl)}">'
            html += f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;">'
            html += f'{_badge(lvl)}'
            # 연구원님 원본 스타일: 사각형 네이비 태그
            html += f'{_tag(item.get("keyword", "응급의료"), "#EAF0FB", "#1B3A6B")}'
            html += f'</div>'
            # ... 타이틀 및 링크 ...